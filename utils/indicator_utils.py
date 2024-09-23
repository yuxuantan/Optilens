import pandas as pd

def get_2day_aggregated_data(data):
    # Ensure the Date column is the index and is of datetime type
    data.index = pd.to_datetime(data.index)

    # if there is odd number of data points, drop the first row in the aggregate calculation
    if len(data) % 2 == 1:
        data = data.iloc[1:]

    # Group data into 2-day periods of price movement (2-day chart)
    grouped = (
        data[["High", "Low", "Open", "Close"]]
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
    aggregated_data = grouped.shift(-1).iloc[::2]
    return aggregated_data


# pass data before kangaroo -1 inside. it cannot take the money of past bear traps
def get_low_inflexion_points(data):
    # get all bear trap dates and values = u or v shape, where T-1 low > T low < T+1 low. Identify T
    all_low_inflexion_points = []
    for i in range(2, len(data) - 2):
        if (
            data["Low"][i - 1] > data["Low"][i] and data["Low"][i] < data["Low"][i + 1]
        ) and (
            data["Low"][i - 2] > data["Low"][i] and data["Low"][i] < data["Low"][i + 2]
        ):
            all_low_inflexion_points.append((data.index[i], data["Low"][i]))
    return all_low_inflexion_points


def get_high_inflexion_points(data):
    all_high_inflexion_points = []
    for i in range(1, len(data) - 2):
        if (
            (data["High"][i - 1] < data["High"][i] and data["High"][i] > data["High"][i + 1])
            and 
            (data["High"][i - 2] < data["High"][i] and data["High"][i] > data["High"][i + 2])
        ):
            all_high_inflexion_points.append((data.index[i], data["High"][i]))
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

def find_lowest_bear_trap_within_price_range(potential_traps, up_to_date, low_price, high_price):
    # Filter bear traps up to the given date
    bear_traps_up_to_date = [(date, low) for date, low in potential_traps if date <= up_to_date]
    
    # For each bear trap, check if it has been invalidated by a higher high
    for date, low in bear_traps_up_to_date:
        # Find if a higher low trap occurred after the bear trap but before the given date
        post_bear_trap_lows = pd.Series([low for trap_date, low in bear_traps_up_to_date if date <= trap_date <= up_to_date])
        if (post_bear_trap_lows < low).any():
            # Bear trap is invalidated
            continue
        # Bear trap is valid
        if low_price <= low <= high_price:
            return(date, low)
    

