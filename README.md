# Electricity Market Optimization App

This project is a decision-making tool based on stochastic optimization for a power producer. It displays the generated scenario prices of the SPOT electricity market and the optimal level of participation in futures and spot electricity markets, hedging price and capacity risk.

## Features

- **Scenario Pool Data Description**: Describes the trajectories of simulated scenario pool prices and their distributions.
- **CVaR vs Expected Profit Analysis**: Shows the trade-off between Conditional Value at Risk (CVaR) and Expected Profit for different risk-aversion levels.
- **Energy Allocation**: Displays the optimal energy allocation between the forward contract and the pool market for different *β* values.
- **Revenues per Market**: Shows the revenues per market given a *β* value.
- **Model Decisions**: Displays the detailed decisions for each time period and scenario based on the optimization model, which can be downloaded as a CSV file for further analysis.


## Files

- [app.py](./app.py): Contains the Streamlit web application code.
- [optimization.py](./optimization.py): Contains the optimization model for the energy trading problem.
- [requirements.txt](./requirements.txt): Lists the required Python packages.
- **Scenarios data**: Contains the scenarios data in CSV format.
- **Time Series Analysis**: Contains the forecasting script in R.

## Data

The data should be in CSV format with the following structure:
- **Date**: The date and time of the price observation.
- **Scenario Columns**: Each column represents a different scenario of pool prices.

## Example

Here is an example of how to use the app:

1. Upload your CSV file containing the scenario pool prices.
2. Navigate to the **CVaR vs Expected Profit Analysis** section to see the trade-off between CVaR and Expected Profit.
3. Adjust the β value using the slider to see how the energy allocation changes in the **Energy Allocation** section.
4. View the revenues per market in the **Revenues per Market** section.
5. Download the detailed model decisions in the **Model Decisions** section.


## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Medafoui/opt-electricity-market.git
    cd opt-electricity-market
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the Streamlit app:
    ```sh
    streamlit run app.py
    ```

2. Upload the forecasted pool prices data in CSV format.

3. Use the sidebar to navigate through different sections of the app:
    - **Scenario Pool Data Description**
    - **CVaR vs Expected Profit Analysis**
    - **Energy Allocation**
    - **Revenues per Market**
    - **Model Decisions**


## Author

Developed by **Mohamed Afif Chifaoui**.

Official GitHub repository: [https://github.com/Medafoui/opt-electricity-market](https://github.com/Medafoui/opt-electricity-market)