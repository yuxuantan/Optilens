
import datetime
import pandas as pd

def get_cumulative_sum_x_days_ago(df, x_days_ago, time_col='trade_time', value_col='profit_usd'):
    today_date = datetime.datetime.now().date()
    x_days_ago_date = today_date - datetime.timedelta(days=x_days_ago)
    x_days_ago_sum = df[df[time_col].dt.date <= x_days_ago_date][value_col].sum()
    return x_days_ago_sum


def parse_contract(contract_str):
    # Example contract string: 'COIN  240823P00197500/OPT/USD'. symbol = COIN, expiry = 24 Aug 2023, strike = 197.5, option_type = PUT
    contract_str = contract_str.replace('/OPT/USD', '')
    symbol = contract_str.split('  ')[0]
    expiry = contract_str.split('  ')[1][:6]
    strike = contract_str.split('  ')[1][-8:]
    option_type = 'CALL' if contract_str.split('  ')[1][6:7] == 'C' else 'PUT'
    return symbol, expiry, strike, option_type


# Identify strategies based on patterns
def identify_strategy(group):

    # Sort by expiry and strike price
    group = group.sort_values(['expiry', 'strike'])
    
    if len(group) == 1:
        row = group.iloc[0]
        if row['opening_qty'] > 0:
            return 'Long Call' if row['option_type'] == 'CALL' else 'Long Put'
        else:
            return 'Short Call' if row['option_type'] == 'CALL' else 'Short Put'
    
    if len(group) == 2:
        if group['option_type'].nunique() == 1:
            # Same type of option, could be a vertical spread
            qty_filled_diff = group['opening_qty'].diff().abs().iloc[1]
            if qty_filled_diff == 0:
                return 'Vertical Spread'
        else:
            # Different types, could be a straddle or strangle
            qty_filled_diff = group['opening_qty'].diff().abs().iloc[1]
            if qty_filled_diff == 0:
                return 'Straddle' if group['strike'].nunique() == 1 else 'Strangle'
    
    # Add more logic for other strategies like Iron Condor, Butterfly, etc.
    
    return 'Complex/Multi-Leg Strategy' if len(group) > 2 else 'Unknown'


# Function to calculate capital used based on strategy
def calculate_capital_used(row):
    if row['strategy'] == 'Long Call' or row['strategy'] == 'Long Put':
        return abs(row['opening_qty']) * row['opening_avg_fill_price'] *100  # Simplified as premium paid
    elif row['strategy'] == 'Short Call' or row['strategy'] == 'Short Put':
        return abs(row['opening_qty']) * (float(row['strike']) / 1000 - row['opening_avg_fill_price']) *100 # Simplified margin
    # elif row['strategy'] == 'Vertical Spread':
    #     return abs(row['qty_filled']) * (row['contract'] - row['contract'])  # Difference in strikes
    # elif row['strategy'] == 'Iron Condor':
    #     return abs(row['qty_filled']) * (row['contract'] - row['contract']) * 2  # Double for Iron Condor
    # else:
    #     return abs(row['qty_filled']) * row['contract']  # Default, can be more specific based on the strategy
    return None


def get_sharpe_ratio(df):
     # Sharpe Ratio: The average return earned in excess of the risk-free rate per unit of volatility or total risk.
    # Assume a constant risk-free rate (annualised) 
    risk_free_rate = 0.01 / 12  # 1% annualised
    # Calculate the monthly return (aggregate by month)
    filled_options_month_df = df.copy()
    filled_options_month_df['month'] = filled_options_month_df['trade_time'].dt.to_period('M')
    filled_options_month_df = filled_options_month_df.groupby('month')['profit_usd'].sum().reset_index()
    filled_options_month_df['month'] = filled_options_month_df['month'].astype(str)
    filled_options_month_df['monthly_return'] = filled_options_month_df['profit_usd'].pct_change()
    # Calculate the excess return (monthly return minus the risk-free rate)
    filled_options_month_df['excess_return'] = filled_options_month_df['monthly_return'] - risk_free_rate


    filled_options_month_df = filled_options_month_df[filled_options_month_df['excess_return'].notna()]
    # remove cases of inf
    filled_options_month_df = filled_options_month_df[~filled_options_month_df['excess_return'].isin([float('inf'), float('-inf')])]

    # Calculate the average of excess returns
    average_excess_return = filled_options_month_df['excess_return'].mean()

    # Calculate the standard deviation of monthly returns (volatility)
    std_dev_return = filled_options_month_df['monthly_return'].std()

    # Calculate the Sharpe Ratio
    sharpe_ratio = average_excess_return / std_dev_return 
    return sharpe_ratio

def get_max_drawdown_pnl(agg_df, agg_df_past):
    # Maximum Drawdown: The largest drop from a peak to a trough in the Cumulative P&L (since there is no portfolio value for options trading)
    agg_df = agg_df.copy()
    # calculate the running maximum of the cumulative P&L
    agg_df['cumulative_profit'] = agg_df['profit_usd'].cumsum()
    # calculate the drawdown (difference between the cumulative profit and the running maximum)
    agg_df['drawdown'] = agg_df['cumulative_profit'] - agg_df['cumulative_profit'].cummax()
    # Calculate the drawdown percentage relative to the running maximum
    agg_df['drawdown_pct'] = (agg_df['drawdown'] / agg_df['cumulative_profit'].cummax()) * 100
    #find the maximum drawdown
    max_drawdown = agg_df['drawdown_pct'].min()


    # calculate the same thing for all data until 30 days ago to compare
    agg_df_past = agg_df_past.copy()
    agg_df_past['cumulative_profit'] = agg_df_past['profit_usd'].cumsum()
    agg_df_past['drawdown'] = agg_df_past['cumulative_profit'] - agg_df_past['cumulative_profit'].cummax()
    agg_df_past['drawdown_pct'] = (agg_df_past['drawdown'] / agg_df_past['cumulative_profit'].cummax()) * 100
    max_drawdown_30_days_ago = agg_df_past['drawdown_pct'].min()
    max_drawdown_change = max_drawdown - max_drawdown_30_days_ago

    return max_drawdown, max_drawdown_change

def get_profit_factor(agg_df, agg_df_past):
     # Profit Factor: The ratio of gross profit to gross loss, indicating overall profitability.
    gross_profit = agg_df[agg_df['profit_usd'] > 0]['profit_usd'].sum()
    gross_loss = agg_df[agg_df['profit_usd'] < 0]['profit_usd'].sum()
    profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else 0
    # calculate the same thing for all data until 30 days ago to compare
    gross_profit_30_days_ago = agg_df_past[agg_df_past['profit_usd'] > 0]['profit_usd'].sum()
    gross_loss_30_days_ago = agg_df_past[agg_df_past['profit_usd'] < 0]['profit_usd'].sum()
    profit_factor_30_days_ago = gross_profit_30_days_ago / abs(gross_loss_30_days_ago) if gross_loss_30_days_ago != 0 else 0
    profit_factor_change = profit_factor - profit_factor_30_days_ago

    return profit_factor, profit_factor_change

def get_win_rate(agg_df, agg_df_past):
    agg_df = agg_df.copy()
    win_rate = round(len(agg_df[agg_df['profit_usd'] > 0]) / len(agg_df) * 100, 2)
    # calculate the same thing for all data until 30 days ago to compare
    agg_df_past = agg_df_past.copy()
    win_rate_30_days_ago = round(len(agg_df_past[agg_df_past['profit_usd'] > 0]) / len(agg_df_past) * 100, 2)
    win_rate_change = round(win_rate - win_rate_30_days_ago, 2)

    return win_rate, win_rate_change

def get_return_on_capital(agg_df, agg_df_past):
    # Apply the capital calculation
    agg_df['capital_used'] = agg_df.apply(calculate_capital_used, axis=1)
    # Calculate Return on Capital
    agg_df['Return on Capital (ROC) %'] = (agg_df['profit_usd'] / agg_df['capital_used']) * 100
    average_roc = agg_df['Return on Capital (ROC) %'].mean()

    # calculate the same thing for all data until 30 days ago to compare
    agg_df_past['capital_used'] = agg_df_past.apply(calculate_capital_used, axis=1)
    agg_df_past['Return on Capital (ROC) %'] = (agg_df_past['profit_usd'] / agg_df_past['capital_used']) * 100
    average_roc_30_days_ago = agg_df_past['Return on Capital (ROC) %'].mean()
    avg_roc_change = average_roc - average_roc_30_days_ago

    return average_roc, avg_roc_change

    