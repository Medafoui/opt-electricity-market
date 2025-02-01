# Description: This file contains the Streamlit web application code for the Electricity Market Optimization App.
import streamlit as st
import pandas as pd
from optimization import run_optimization 
import plotly.graph_objects as go
import plotly.express as px
import numpy as np  



st.title("Electricity Market Optimization :chart_with_upwards_trend:")


st.image('images/power.jpg')

st.divider()

st.markdown(
"""
:rocket: Welcome to the **Electricity Market Optimization App**, a decision-making tool based on stochastic optimization for a power producer. It displays the simulated scenario prices of the SPOT electricity market for October and 
the optimal level of participation in futures and spot electricity markets hedging price and capacity risk.
<div style="margin-top:30px;"></div>


:bulb: **Features**
- **Scenario pool data description**: this section describes the trajectories of simulated scenario pool prices for the month of October and their distributions.
- **CVaR vs Expected Profit Analysis**: this section shows the trade-off between Conditional Value at Risk (CVaR) and Expected Profit for different risk-aversion levels.
- **Energy Allocation**: this section displays the optimal energy allocation between the forward contract and the pool market for different $\\beta$ values.
- **Revenues per market**: this section shows the revenues per market given a $\\beta$ value.
- **Model Decisions**: this section displays the detailed decisions for each time period and scenario based on the optimization model which can be downloaded as a CSV file for further analysis.



:computer: **Developer**
- This web application has been developed by **Mohamed Afif Chifaoui**.
- Official GitHub repository of the app: [](https://github.com/Medafoui/opt-electricity-market)

"""
, unsafe_allow_html=True
)

st.divider()


# File uploader for CSV
st.sidebar.header("Input Data :open_file_folder:")
uploaded_file = st.sidebar.file_uploader("Upload Scenarios File", type=["csv"])


#----------------------------------------------------------------
st.sidebar.header('Contents')
#----------------------------------------------------------------

if st.sidebar.checkbox('Scenario pool data description'):

    st.markdown('### Scenario SPOT prices description')

    st.markdown("""
    :bar_chart: The **data** was created by fitting an ARIMA model to the months of August and September of 2024 and then generate pool prices for the following month October.
                As a result of this, we have scenarios of pool prices for this month to be the input of the PyoMo optimization model and get the optimal decisions for the power producer.
                Dimension of the data is 10 scenarios (columns) and 720 hours (rows). 
                """)

    if uploaded_file is not None:
        # Read and preprocess the CSV file 
        scenarios_df = pd.read_csv(uploaded_file)
        df_info = scenarios_df.copy() # create a copy of the original df in case we need to add new columns
        
        # Ensure the 'Date' column is present and convert it to datetime
        if 'Date' in df_info.columns:
            df_info['datetime'] = pd.to_datetime(df_info['Date'])
            df_info = df_info.drop(columns=['Date'])
            df_info.set_index('datetime', inplace=True)
            

        
        # Display the preprocessed data table
        st.markdown("#### SPOT scenario prices")
        st.write(scenarios_df)
        
        df_info['Average_Price'] = df_info.mean(axis=1)

        # Dropdown for selecting the plot
        plot_options = [
            "Scenario Trajectories",
            "Time Series of Average Spot Prices",
            "Histogram of Pool Price Distribution",
            "Boxplot of Pool Prices",
        ]
        selected_plot = st.selectbox("Select a plot to display:", plot_options)

        if selected_plot == "Scenario Trajectories":
            # Create the "Scenario Trajectories" plot
            fig = go.Figure()

            # Loop through each scenario column in the DataFrame and add a line plot
            for scenario in df_info.columns:
                if scenario != 'Average_Price':  # Exclude the 'Average_Price' column
                    fig.add_trace(go.Scatter(
                        x=df_info.index,  
                        y=df_info[scenario],
                        mode='lines',
                        name=scenario,
                        hovertemplate='%{y:.2f} €/MWh<br>Date: %{x}'
                    ))

            # Update the layout of the figure
            fig.update_layout(
                title="Scenario Trajectories",
                xaxis_title="Date",
                yaxis_title="Price (€/MWh)",
                template="plotly_white",
                xaxis=dict(
                    tickformat="%d-%b %H:%M",  
                ),
                legend_title="Scenarios"
            )

            # Show the plot
            st.plotly_chart(fig)

        elif selected_plot == "Time Series of Average Spot Prices":
            # Create a time series plot of the average spot prices
            fig_time_series = go.Figure()

            # Add a line trace for the average spot price
            fig_time_series.add_trace(go.Scatter(
                x=df_info.index,  # Assuming DataFrame index is DateTime
                y=df_info['Average_Price'],
                mode='lines',
                name='Average Spot Price',
                hovertemplate='%{y:.2f} €/MWh<br>Date: %{x}'  
            ))

            # Update layout to improve readability
            fig_time_series.update_layout(
                title="Time Series of Average Spot Prices",
                xaxis_title="Datetime",
                yaxis_title="Average Spot Price (€)",
                template="plotly_white",
                xaxis=dict(
                    tickformat="%d-%b %H:%M",  # Format for date-time axis
                ),
                legend_title="Legend"
            )

            # Show the plot
            st.plotly_chart(fig_time_series)

        elif selected_plot == "Histogram of Pool Price Distribution":
            # Create a histogram of pool price distribution
            pool_prices = df_info.values.flatten()  # Flatten to create a single array of prices

            fig_histogram = px.histogram(
                x=pool_prices,
                nbins=50,  
                labels={'x': 'Price (€/MWh)'},
                title="Distribution of Pool Prices"
            )

            # Update layout to improve readability
            fig_histogram.update_layout(
                template="plotly_white",
                xaxis=dict(
                    title="Price (€/MWh)"
                ),
                yaxis=dict(
                    title="Frequency"
                )
            )

            # Show the plot
            st.plotly_chart(fig_histogram)


        elif selected_plot == "Boxplot of Pool Prices":
            # Reshape DataFrame for Plotly
            reshaped_df = scenarios_df.melt(var_name="Scenario", value_name="Price (€/MWh)")
            
            # Use Plotly to create the boxplot
            fig = px.box(
                reshaped_df,
                x="Scenario",  # Each scenario on the x-axis
                y="Price (€/MWh)",  # Prices on the y-axis
                title="Boxplot of Pool Prices Per Scenario",
            )
            
            fig.update_layout(
                xaxis_title="Scenario",
                yaxis_title="Price (€/MWh)",
                boxmode="group",  # Group the boxes for clarity
                template="plotly_white"
            )
            
            # Render the Plotly figure in Streamlit
            st.plotly_chart(fig, use_container_width=True)

            # Add success message for feedback
            st.success("File uploaded and preprocessed successfully!")

        else:
            st.error("The uploaded file must contain a 'Date' column.")
            st.stop()  # Stop the execution if the format is invalid
    else:
        st.stop()  # Stop further execution until a file is uploaded




#------------------------CVAR VS EXPECTED PROFIT-------------------------------------------------------------------------------------------

if st.sidebar.checkbox('CVaR vs Expected Profit'):

    st.markdown('### CVaR vs Expected Profit Analysis')

    st.markdown("""
    :mag:  $\\beta$ factor is directly proportional to risk-aversion. This means that the higher the value of $\\beta$, the decision-maker tends to choose safer options and less volatile
                options such as selling in the SPOT market. Hence, the **expected profit** will be lower and the **Conditional Value at Risk (CVaR)** higher. Let us verify that in the following plot:
                """)

    if uploaded_file:
        beta_values = np.arange(0, 1.1, 0.1)  # Define beta values range

        
        results = run_optimization(scenarios_df, beta_values)  # Get the optimization results
        # print(results)
        cvar_values = results['cvar_values']
        profit_values = results['profit_values']



        # Add CVaR vs Profit Plot
        fig_cvar_profit = go.Figure()

        fig_cvar_profit.add_trace(
            go.Scatter(
                x=cvar_values,
                y=profit_values,
                mode='lines+markers+text',
                marker=dict(size=8, color='green'),
                line=dict(dash='dash', color='green'),
                name='Expected Profit vs CVaR',
                text=[f"β = {round(beta, 2)}" for beta in beta_values],
                textposition='top center',
                hovertemplate="<b>β:</b> %{text}<br><b>CVaR (€):</b> %{x}<br><b>Profit (€):</b> %{y}<extra></extra>",
            )
        )

        fig_cvar_profit.update_layout(
            title=dict(
            text="CVaR vs Expected Profit Analysis",  # Set the title of the plot       
            ),

            xaxis=dict(
                title="CVaR (€)",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                showgrid=True,
                gridcolor='lightgray',
            ),
            yaxis=dict(
                title="Expected Profit (€)",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                showgrid=True,
                gridcolor='lightgray',
            ),
            template="plotly_white",
            legend=dict(font=dict(size=12)),
        )

        st.plotly_chart(fig_cvar_profit)




#-----------------------ENERGY ALLOCATION----------------------------------------------------------------------------------------------------

if st.sidebar.checkbox('Energy Allocation'):

    if uploaded_file:
    
        # Energy Allocation Plot
        st.subheader("Energy Allocation")

        beta = st.slider('Select a beta to see energy allocation', 0.0, 1.0, .1)  # Slider for selecting beta
        selected_results = run_optimization(scenarios_df, beta)  # Run for the selected beta

        labels = ['Forward Contract', 'Pool Market']
        sizes = [selected_results['sold_energy_forward'], selected_results['sold_energy_pool']]
        colors = ['red', 'palegreen']

        fig_energy_allocation = go.Figure()
        fig_energy_allocation.add_trace(
            go.Pie(labels=labels,
            values=sizes,
            marker=dict(colors=colors),  # Custom colors
            textinfo='label+percent',  # Display labels and percentages
            hovertemplate="<b>%{label}</b><br>Energy: %{value} MW<extra></extra>",  # Custom hover text
            insidetextorientation='radial',  # Position text
            hole=0.4)
        )
        fig_energy_allocation.update_layout(title="Energy Allocation")
        st.plotly_chart(fig_energy_allocation)




#-----------------------REVENUES PER MARKET-------------------------------------------------------------------------------------------


if st.sidebar.checkbox('Revenues per market :euro:'):

    st.markdown('### Revenues per Market')

    if uploaded_file:
        # Run optimization for a specific beta 
        beta = st.slider('Select a beta to see revenues in both markets', 0.0, 1.0, 0.1)  # Slider for beta
        results = run_optimization(scenarios_df, beta)  

        forward_revenues = results['total_forward_revenue']
        pool_revenues = results['total_pool_revenue']



        # Data for the bar plot
        categories = ['Forward Market Revenue', 'Pool Market Revenue']
        values = [forward_revenues,pool_revenues]

        # Create a Plotly bar chart
        fig_bar = go.Figure()

        fig_bar.add_trace(
            go.Bar(
                x=categories,
                y=values,
                marker=dict(color=['red', 'palegreen']),
                text=values,
                textposition='auto',
                hovertemplate="<b>%{x}</b><br>Revenue: %{y:.2f} €<extra></extra>",
            )
        )

        # Update layout
        fig_bar.update_layout(
            title="Revenue Breakdown: Forward Market vs Pool Market",
            title_font=dict(size=18),
            xaxis=dict(
                title="Market",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
            ),
            yaxis=dict(
                title="Revenue (€)",
                titlefont=dict(size=14),
                tickfont=dict(size=12),
                showgrid=True,  # Show gridlines for better readability
                gridcolor='lightgray',  # Light color for the gridlines
            ),
            template="plotly_white",
        )

        st.plotly_chart(fig_bar)



#-------------------------------MODEL DECISIONS---------------------------------------------------------------------------------------------------

if st.sidebar.checkbox('Model Decisions'):

    st.markdown('### Optimization Results')

    if uploaded_file:
        # Run optimization for a specific beta 
        beta = st.slider('Select a beta for optimization (0 to 1)', 0.0, 1.0, 0.1)  # Slider for beta
        model, results = run_optimization(scenarios_df, beta, return_model=True) 
       

        # Extract optimization parameters for display
        future_contract_price = model.lambda_F[1]
        max_generation_capacity = model.PG_max[1]
        cost_per_unit = model.C_G[1]
        max_forward_sales = model.PF_max[1]

        # Display parameter data in styled boxes
        st.markdown("""
        <div style="background-color:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:20px;">
            <h3 style="color:#4CAF50; margin-top:0;">Optimization Parameters</h3>
            <ul style="list-style-type:none; padding-left:0;">
                <li><b>Price of Future Contract:</b> {future_price} €/MWh</li>
                <li><b>Max Power Generation Capacity:</b> {max_gen_capacity} MWh</li>
                <li><b>Cost Per Unit:</b> {cost_unit} €/MWh</li>
                <li><b>Max Forward Sales:</b> {max_forward_sales} MWh</li>
            </ul>
        </div>
        """.format(
            future_price=future_contract_price,
            max_gen_capacity=max_generation_capacity,
            cost_unit=cost_per_unit,
            max_forward_sales=max_forward_sales
        ), unsafe_allow_html=True)


       
        # Display the model decisions
        st.markdown(f"""
        For β = {beta}, here are the detailed decisions for each time period and scenario:
        """)

        # Create a DataFrame to store decisions
        data = []
        for t in model.T:
            for w in model.Omega:
                forward_energy = model.PF[1].value  # Energy sold in forward contract
                pool_energy = model.EP[t, w].value  # Energy sold in pool market
                generation_energy = model.EG[1, t, w].value  # Energy generated
                contract_price = model.lambda_F[1]  # Forward contract price
                pool_price = model.lambda_P[t, w]  # Pool price

                data.append({
                    "Time": t,
                    "Scenario": w,
                    "Forward Energy (MWh)": forward_energy,
                    "Pool Energy (MWh)": pool_energy,
                    "Generation Energy (MWh)": generation_energy,
                    "Contract Price (€/MWh)": contract_price,
                    "Pool Price (€/MWh)": pool_price
                })

        decisions_df = pd.DataFrame(data)

        # Display the DataFrame as a table
        st.dataframe(decisions_df)

        # Add a download button for decisions
        csv = decisions_df.to_csv(index=True)
        st.download_button(
            label="Download Decisions as CSV",
            data=csv,
            file_name=f"decisions_beta_{beta}.csv",
            mime="text/csv"
        )

        # Add expandable details for each time period
        for t in model.T:
            with st.expander(f"Time Period {t} Details"):
                for w in model.Omega:
                    st.write(f"**Scenario {w}:**")
                    st.write(f"- Forward Energy: {model.PF[1].value} MWh")
                    st.write(f"- Pool Energy: {model.EP[t, w].value} MWh")
                    st.write(f"- Generation Energy: {model.EG[1, t, w].value} MWh")
                    st.write(f"- Pool Price: {model.lambda_P[t, w]} €/MWh")
                    st.write("-" * 50)

        st.success("Model decisions displayed successfully!")
    else:
        st.warning("Please upload a scenarios file to proceed with model decisions.")
