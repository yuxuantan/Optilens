import pandas as pd

def get_2day_aggregated_data(data):
    # Ensure the Date column is the index and is of datetime type
    data.index = pd.to_datetime(data.index)
    
    # Split the data into separate dataframes by year
    yearly_data = {year: df for year, df in data.groupby(data.index.year)}
    
    aggregated_data_list = []
    
    # Process each year's dataframe independently
    for year, df in yearly_data.items():
        # Group data into 2-day periods within each year
        grouped = (
            df[["High", "Low", "Open", "Close"]]
            .rolling(window=2, min_periods=1)
            .agg(
                {
                    "High": "max",
                    "Low": "min",
                    "Open": lambda x: x.iloc[0],
                    "Close": lambda x: x.iloc[-1],
                }
            )
        )
        # Shift to make the aggregation align to the end of each 2-day period
        aggregated = grouped.shift(-1).iloc[::2]
        
        # Append the result for the current year
        aggregated_data_list.append(aggregated)

    # Combine all the yearly dataframes into one dataframe
    if aggregated_data_list:
        aggregated_data = pd.concat(aggregated_data_list)
    else:
        aggregated_data = pd.DataFrame()
    
    return aggregated_data


# pass data before kangaroo -1 inside. it cannot take the money of past bear traps
def get_low_inflexion_points(data):
    # get all bear trap dates and values = u or v shape, where T-1 low > T low < T+1 low. Identify T
    all_low_inflexion_points = []
    for i in range(2, len(data) - 2):
        if (
            data.iloc[i - 1]["Low"] > data.iloc[i]["Low"] < data.iloc[i + 1]["Low"]
        ) and (
            data.iloc[i - 2]["Low"] > data.iloc[i]["Low"] < data.iloc[i + 2]["Low"]
        ):
            all_low_inflexion_points.append((data.index[i], data.iloc[i]["Low"]))
    return all_low_inflexion_points


def get_high_inflexion_points(data):
    all_high_inflexion_points = []
    for i in range(2, len(data) - 2):
        if (
            (data.iloc[i - 1]["High"] < data.iloc[i]["High"] > data.iloc[i + 1]["High"])
            and 
            (data.iloc[i - 2]["High"] < data.iloc[i]["High"] > data.iloc[i + 2]["High"])
        ):
            all_high_inflexion_points.append((data.index[i], data.iloc[i]["High"]))
    return all_high_inflexion_points


def find_bear_traps(potential_traps, from_date, to_date):
    bear_traps = []
    # Filter bear traps up to the given date
    bear_traps_up_to_date = [(date, low) for date, low in potential_traps if from_date <= date <= to_date]

    # For each bear trap, check if it has been invalidated by a higher high
    for date, low in bear_traps_up_to_date:
        # Find if a higher low trap occurred after the bear trap but before the given date
        post_bear_trap_lows = pd.Series([low for trap_date, low in bear_traps_up_to_date if date <= trap_date <= to_date])
        if (post_bear_trap_lows < low).any():
            # Bear trap is invalidated
            continue
        bear_traps.append((date, low))

        # Bear trap is valid
    return bear_traps

def find_bull_traps(potential_traps, from_date, to_date):
    bull_traps = []
    # Filter bull traps up to the given date
    bull_traps_up_to_date = [(date, high) for date, high in potential_traps if from_date <= date <= to_date]

    # For each bull trap, check if it has been invalidated by a lower low
    for date, high in bull_traps_up_to_date:
        # Find if a lower high trap occurred after the bull trap but before the given date
        post_bull_trap_highs = pd.Series([high for trap_date, high in bull_traps_up_to_date if date <= trap_date <= to_date])
        if (post_bull_trap_highs > high).any():
            # Bull trap is invalidated
            continue
        bull_traps.append((date, high))

        # Bull trap is valid
    return bull_traps


# def find_lowest_bear_trap_within_price_range(potential_bear_traps, high_point_date, low_price, high_price):
#     active_traps = []
#     for trap in potential_bear_traps:
#         trap_date, trap_low = trap
#         if trap_date >= high_point_date or not (low_price < trap_low < high_price):
#             continue
        
#         # Invalidate older traps with higher lows
#         active_traps = [t for t in active_traps if t[1] < trap_low]
#         active_traps.append(trap)
    
#     return min(active_traps, key=lambda x: x[1]) if active_traps else None
    



def find_lowest_bear_trap_within_price_range(potential_traps, up_to_date, low_price, high_price):
    # from date is 1 year before up_to_date
    from_date = up_to_date - pd.DateOffset(years=1)
    # Filter bear traps up to the given date
    bear_traps_up_to_date = find_bear_traps(potential_traps, from_date=from_date, to_date=up_to_date)
    
    for date, low in bear_traps_up_to_date:
        # Bear trap is valid
        if low_price <= low <= high_price:
            return(date, low)
    

def find_highest_bull_trap_within_price_range(potential_traps, up_to_date, low_price, high_price):
    from_date = up_to_date - pd.DateOffset(years=1)
    # Filter bull traps up to the given date
    bull_traps_up_to_date = find_bull_traps(potential_traps, from_date=from_date, to_date=up_to_date)

    for date, high in bull_traps_up_to_date:
        # Bull trap is valid
        if low_price <= high <= high_price:
            return(date, high)
