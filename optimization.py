# Description: This file contains the optimization model for the energy trading problem.
import pandas as pd
from pyomo.environ import ConcreteModel, Var, Param, NonNegativeReals, RangeSet, Objective, Constraint, SolverFactory, maximize, Reals
from pyomo.opt import SolverStatus, TerminationCondition
import numpy as np
from tqdm import tqdm
import os
import streamlit as st
import gurobipy as gp


# # Set up the Gurobi environment with WLS credentials
# os.environ["GRB_WLSACCESSID"] = st.secrets["GRB_WLSACCESSID"]
# os.environ["GRB_WLSSECRET"] = st.secrets["GRB_WLSSECRET"]
# os.environ["GRB_LICENSEID"] = st.secrets["GRB_LICENSEID"]



# # Locally
# from dotenv import load_dotenv
# load_dotenv()

# # Get the values safely
# wls_access_id = os.getenv("GRB_WLSACCESSID")
# wls_secret = os.getenv("GRB_WLSSECRET")
# license_id = os.getenv("GRB_LICENSEID")

# # Ensure they are not None before setting them
# if not wls_access_id or not wls_secret or not license_id:
#     raise ValueError("Gurobi WLS credentials are missing. Please check your environment variables.")

# os.environ["GRB_WLSACCESSID"] = wls_access_id
# os.environ["GRB_WLSSECRET"] = wls_secret
# os.environ["GRB_LICENSEID"] = license_id



def run_optimization(scenarios, beta, return_model=False):
    """
    Run the optimization for the given scenarios and beta value(s).
    If beta is a single value, the optimization runs for that value.
    If beta is a list/array, it runs for each value in the array.

    Parameters:
    - scenarios: A pandas DataFrame containing the scenario prices and datetime index.
    - beta: A risk aversion parameter (float) or a list/array of values.
    - return_model: A boolean flag indicating whether to return the Pyomo model or not.

    Returns:
    - If beta is a single value:
      A dictionary containing the optimization results for that beta.
    - If beta is a list/array:
      A dictionary containing beta values, CVaR values, expected profit, and energy allocation.
    - If return_model is True:
        A tuple containing the Pyomo model and the optimization results.
    """


    scenarios['datetime'] = pd.to_datetime(scenarios['Date'])
    scenarios = scenarios.drop(columns=['Date'])
    scenarios.set_index('datetime', inplace=True)


    # First we slice the df to retrieve only the last week of data (last 168 observations)
    scenarios_df = scenarios.copy()  # Copy the DataFrame to avoid modifying the original
    scenarios_df = scenarios_df.iloc[-168:]  

    # Initialize the Pyomo model
    model = ConcreteModel()

    # Define Sets based on the DataFrame
    model.T = RangeSet(1, 168)  # Time periods
    model.Omega = RangeSet(1, len(scenarios_df.columns))  # Scenarios w1, w2, ..., wn
    model.F = RangeSet(1, 1)  # Forward contracts (assuming 1 forward contract)
    model.G = RangeSet(1, 1)  # Generation (assuming 1 generation unit)



    # Convert DataFrame to a dictionary where each (t, w) key pairs with a price covering 168 times and 10 scenarios
    pool_prices_dict = {
        (t + 1, w + 1): scenarios_df.iloc[t, w]  # Adjust to ensure that we cover all time periods (1 to 168) and scenarios (1 to 10)
        for t in range(scenarios_df.shape[0])  # 168 time periods (rows in the DataFrame)
        for w in range(scenarios_df.shape[1])  # 10 scenarios (columns in the DataFrame)
    }


    # Parameters
    model.lambda_F = Param(model.F, initialize={1: 350})  # Forward price (fixed)
    model.lambda_P = Param(model.T, model.Omega, initialize=pool_prices_dict)  # Pool prices from last_week_df
    model.C_G = Param(model.G, initialize={1: 45})  # Generation cost per unit
    model.PF_max = Param(model.F, initialize=250)  # Max forward sales
    model.PG_max = Param(model.G, initialize={1: 500})  # Max generation capacity
    model.beta = Param(initialize=0.1, mutable=True)  # Risk aversion parameter
    model.alpha = Param(initialize=0.7)  # Confidence level for CVaR
    model.pi = Param(model.Omega, initialize={w: 1 / len(scenarios_df.columns) for w in model.Omega})  # Scenario probability


    # Decision Variables
    model.PF = Var(model.F, within=NonNegativeReals)  # Forward market sales
    model.EP = Var(model.T, model.Omega, within=NonNegativeReals)  # Pool market energy allocation
    model.EG = Var(model.G, model.T, model.Omega, within=NonNegativeReals)  # Generation energy allocation
    model.zeta = Var(within=Reals)  # CVaR value
    model.eta = Var(model.Omega, within=NonNegativeReals)  # CVaR auxiliary variable


    # Objective Function
    def objective_rule(model):
        expected_profit = (1 - model.beta) * sum(
            model.pi[w] * (
                sum(model.lambda_F[f] * model.PF[f] for f in model.F for t in model.T) +  # forward revenues
                sum(model.lambda_P[t, w] * model.EP[t, w] for t in model.T) -  # pool revenues
                sum(model.C_G[1] * model.EG[1, t, w] for t in model.T)  # cost of production
            )
            for w in model.Omega
        )
        cvar_adjustment = model.beta * (
            model.zeta - (1 / (1 - model.alpha)) * sum(model.pi[w] * model.eta[w] for w in model.Omega)
        )
        return expected_profit + cvar_adjustment
    model.obj = Objective(rule=objective_rule, sense=maximize)


    # Constraints
    def forward_contracts_rule(model, f):
        return (0, model.PF[f], model.PF_max[f])
    model.ForwardContracts = Constraint(model.F, rule=forward_contracts_rule)

    def generation_capacity_rule(model, t, w):
        return (0, model.EG[1, t, w], model.PG_max[1])
    model.GenerationCapacity = Constraint(model.T, model.Omega, rule=generation_capacity_rule)

    def energy_balance_rule(model, t, w):
        return model.EG[1, t, w] == model.EP[t, w] + sum(model.PF[f] for f in model.F)
    model.EnergyBalance = Constraint(model.T, model.Omega, rule=energy_balance_rule)

    def cvar_constraint_rule(model, w):
        return model.zeta - (
            sum(model.lambda_F[f] * model.PF[f] for f in model.F) +
            sum(model.lambda_P[t, w] * model.EP[t, w] for t in model.T) -
            sum(model.C_G[g] * model.EG[g, t, w] for g in model.G for t in model.T)) <= model.eta[w]
    model.CVaRConstraint = Constraint(model.Omega, rule=cvar_constraint_rule)

    def cvar_nonnegativity_rule(model, w):
        return model.eta[w] >= 0
    model.CVaRNonnegativity = Constraint(model.Omega, rule=cvar_nonnegativity_rule)


    # Solver
    # solver = SolverFactory('gurobi')

    # Set up the Gurobi environment with WLS credentials
    # env = gp.Env(
    #     params={
    #     "WLSACCESSID": os.getenv("GRB_WLSACCESSID"),
    #     "WLSSECRET": os.getenv("GRB_WLSSECRET"),
    #     "LICENSEID": int(os.getenv("GRB_LICENSEID", 0)),  # Ensure it's an integer
    #     }
    # )

    env = gp.Env(
        params={
        "WLSACCESSID": st.secrets["GRB_WLSACCESSID"],
        "WLSSECRET": st.secrets["GRB_WLSSECRET"],
        "LICENSEID": int(st.secrets["GRB_LICENSEID"]),  # Ensure it's an integer
        }
    )

    # Create the solver with the Gurobi environment
    solver = SolverFactory('gurobi', solver_io="python", env=env)


    # If beta is a single value, perform computation for just that beta
    if isinstance(beta, (float, int)):
        model.beta.set_value(beta)
        results = solver.solve(model, tee=False)
        sold_energy_forward = sum(model.PF[1].value for f in model.F for t in model.T)
        sold_energy_pool = sum(model.EP[t, w].value for t in model.T for w in model.Omega)
        total_forward_revenue =  (sum(model.lambda_F[f] * model.PF[f].value for f in model.F for t in model.T))
        total_pool_revenue =  sum(model.lambda_P[t, w] * model.EP[t, w].value for t in model.T for w in model.Omega)  


        if return_model:
            return model, {
                'sold_energy_forward': sold_energy_forward,
                'sold_energy_pool': sold_energy_pool,
            }

        return {
            'sold_energy_forward': sold_energy_forward,
            'sold_energy_pool': sold_energy_pool,
            'total_forward_revenue': total_forward_revenue,
            'total_pool_revenue': total_pool_revenue,
        }
    


    # If beta is a list/array, perform computation for all beta values
    beta_values = np.array(beta)
    cvar_values = []
    profit_values = []
    obj_values = []
    pf_values = []

    progress_bar = st.progress(0)  # Initialize Streamlit progress bar

    for i, b in enumerate(beta_values):

    # for b in tqdm(beta_values, desc='Processing for Beta values'):
        model.beta.set_value(b)
        # results = solver.solve(model, tee=True)
        results = solver.solve(model)
        model_expected_profit = sum(
            model.pi[w] * (
                sum(model.lambda_F[f] * model.PF[f].value for f in model.F for t in model.T) +
                sum(model.lambda_P[t, w] * model.EP[t, w].value for t in model.T) -
                sum(model.C_G[1] * model.EG[1, t, w].value for t in model.T)
            ) for w in model.Omega
        )
        cvar = model.zeta.value - (1 / (1 - model.alpha)) * sum(model.pi[w] * model.eta[w].value for w in model.Omega)

        
        obj_values.append(model.obj())
        cvar_values.append(cvar)
        profit_values.append(model_expected_profit)
        pf_values.append(model.PF[1].value)

    # Update the progress bar
    progress_bar.progress((i + 1) / len(beta_values))

    results_dict = {
        'beta_values': beta_values,
        'cvar_values': cvar_values,
        'profit_values': profit_values,
        'pf_values': pf_values,
    }

    if return_model:
        return model, results_dict
    
    return results_dict
