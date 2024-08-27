
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