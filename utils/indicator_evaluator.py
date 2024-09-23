import pandas as pd
from typing import List, Dict
import streamlit as st
from datetime import datetime
import utils.ticker_getter as tg


def analyze_stock(ticker: str, settings: Dict[str, int]) -> List[str]:
    """Analyze a stock and return notifications based on user preferences."""
    print(ticker)
    data = tg.fetch_stock_data(ticker, period="max", interval="1d")

    # Filter out indicator settings with is_enabled = False
    enabled_settings = {
        k: v for k, v in settings["indicator_settings"].items() if v["is_enabled"]
    }

    # Store dates where each indicator's condition is met
    indicator_dates = {}

    # get the date x trading days before last day in stock data
    recency_cutoff_date = None
    if len(data.index) > 0:
        recency_cutoff_date = data.index[-min(settings["recency"], len(data.index) - 1)]

    # Check enabled indicators and get the dates where the condition is met
    for indicator, config in enabled_settings.items():
        dates = None
        if indicator == "golden_cross_sma":
            dates = get_golden_cross_sma_dates(
                data, config["short_sma"], config["long_sma"]
            )
        elif indicator == "death_cross_sma":
            dates = get_death_cross_sma_dates(
                data, config["short_sma"], config["long_sma"]
            )
        elif indicator == "rsi_overbought":
            dates = get_rsi_overbought_dates(data, config["threshold"])
        elif indicator == "rsi_oversold":
            dates = get_rsi_oversold_dates(data, config["threshold"])
        elif indicator == "macd_bullish":
            dates = get_macd_bullish_dates(
                data, config["short_ema"], config["long_ema"], config["signal_window"]
            )
        elif indicator == "macd_bearish":
            dates = get_macd_bearish_dates(
                data, config["short_ema"], config["long_ema"], config["signal_window"]
            )
        elif indicator == "bollinger_squeeze":
            dates = get_bollinger_band_squeeze_dates(
                data, config["window"], config["num_std_dev"]
            )
        elif indicator == "bollinger_expansion":
            dates = get_bollinger_band_expansion_dates(
                data, config["window"], config["num_std_dev"]
            )
        elif indicator == "bollinger_breakout":
            dates = get_bollinger_band_breakout_dates(
                data, config["window"], config["num_std_dev"]
            )
        elif indicator == "bollinger_pullback":
            dates = get_bollinger_band_pullback_dates(
                data, config["window"], config["num_std_dev"]
            )
        elif indicator == "volume_spike":
            dates = get_volume_spike_dates(
                data, config["window"], config["num_std_dev"]
            )
        elif indicator == "apex_bull_appear":
            dates = get_apex_bull_appear_dates(data)
        elif indicator == "apex_bear_appear":
            dates = get_apex_bear_appear_dates(data)
        elif indicator == "apex_uptrend":
            dates = get_apex_uptrend_dates(data)
        elif indicator == "apex_downtrend":
            dates = get_apex_downtrend_dates(data)
        elif indicator == "apex_bull_raging":
            dates = get_apex_bull_raging_dates(data)

        # If no dates are found, skip this indicator
        if dates is None or len(dates) == 0:
            return None

        ## if the latest date does not exist in the data, return None
        # if (dates[-1] != data.index[-1]):
        #     return None

        # last indicator appear date
        last_date_detected = dates[-1]

        # check the last x dates using index
        if last_date_detected < recency_cutoff_date:
            return None

        indicator_dates[indicator] = dates

    # Find common dates between all enabled indicators
    common_dates = set(data.index)
    for dates in indicator_dates.values():
        common_dates.intersection_update(dates)

    common_dates = sorted(common_dates)  # Sort dates for clarity

    success_count = 0

    avg_percentage_change = 0
    valid_count = 0  # To keep track of how many valid instances we have

    for date in common_dates:
        index_of_date = data.index.get_loc(date)

        if index_of_date + settings["x"] >= len(data.index):
            continue

        target_date_for_metric_calculation = data.index[index_of_date + settings["x"]]
        # Calculate the success rate based on provided logic
        if (target_date_for_metric_calculation) in data.index and data.loc[
            target_date_for_metric_calculation, "Close"
        ] > data.loc[date, "Close"]:
            success_count += 1

        # Calculate the average percentage change
        if date in data.index and target_date_for_metric_calculation in data.index:
            try:
                current_close = data.loc[date, "Close"]
                future_close = data.loc[target_date_for_metric_calculation, "Close"]
                percentage_change = (future_close - current_close) / current_close * 100
                avg_percentage_change += percentage_change
                valid_count += 1
            except KeyError:
                # Handle the case where 'Close' might not be in the DataFrame (unlikely but for completeness)
                print(
                    f"Missing 'Close' price for date: {date} or {target_date_for_metric_calculation}"
                )
        else:
            print(
                f"Date {date} or {target_date_for_metric_calculation} is not in the DataFrame"
            )

    total_instances = len(common_dates)
    success_rate = (success_count / total_instances * 100) if total_instances > 0 else 0

    # Calculate the average percentage change if there are valid instances
    avg_percentage_change = (
        avg_percentage_change / valid_count if valid_count > 0 else 0
    )

    # Compile results
    result = {
        "common_dates": [str(date) for date in common_dates],
        "total_instances": total_instances,
        "success_rate": success_rate,
        "avg_percentage_change": avg_percentage_change,
    }

    return result


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
    


if __name__ == "__main__":
    import ticker_getter as tg

    data = get_2day_aggregated_data(
        tg.fetch_stock_data("CPRT", period="max", interval="1d")
    )
def get_apex_bull_raging_dates(data):
    print("I'm in")
    data = get_2day_aggregated_data(data)

    high_inflexion_points = get_high_inflexion_points(data)
    potential_bear_traps = get_low_inflexion_points(data)

    bull_raging_dates = []

    for high_point in high_inflexion_points:
        high_point_date, high_point_value = high_point
        print(f"checking {high_point_date}:")
        if high_point_date not in data.index:
            continue

        
        # Find the stopping point (which is the next bear trap)
        stopping_point_date = None
        for bear_trap in potential_bear_traps:
            if bear_trap[0] > high_point_date:
                stopping_point_date = bear_trap[0]
                break
        if stopping_point_date is None:
            stopping_point_date = data.index[-1]
        print(f"stopping point date: {stopping_point_date}")

        previous_bear_trap = find_lowest_bear_trap_within_price_range(potential_bear_traps, high_point_date, data.loc[stopping_point_date]["Low"], high_point_value)
        # if len(bear_traps) < 2:
        #     continue
        # previous_bear_trap = bear_traps[-2]

        if previous_bear_trap is None:
            continue
        print(f"previous_bear_trap: {previous_bear_trap}")

        mid_point = previous_bear_trap[1] + (high_point_value - previous_bear_trap[1]) / 2

        # Analyze the range from high point to stopping point
        range_data = data.loc[high_point_date:stopping_point_date]
        flush_down_bars = range_data[
            (range_data['Open'] - range_data['Close']) > 0.7 * (range_data['High'] - range_data['Low'])
        ]

        if len(flush_down_bars) == 0 or flush_down_bars.iloc[0]['High'] < mid_point:
            print("❌ first flush down started after mid point, or didn't happen at all")
            continue
        else:
            print(f"✅ first flush down started at {flush_down_bars.iloc[0]['High']} before mid point {mid_point}")

        # Find the date which broke below bear trap
        break_below_bear_trap = range_data[range_data['Low'] < previous_bear_trap[1]].index
        if len(break_below_bear_trap) == 0:
            print(f"❌ no break below bear trap {previous_bear_trap} before the price reaches stopping point")
            continue
        date_which_broke_below_bear_trap = break_below_bear_trap[0]
        print(f"✅ date_which_broke_below_bear_trap: {date_which_broke_below_bear_trap}")

        total_bar_count = len(range_data)
        if total_bar_count < 5 or len(flush_down_bars) / total_bar_count < 0.2:
            print(f"❌ less than 5 bars or not majority flush down, flush down bars: {len(flush_down_bars)}, total bars: {total_bar_count}")
            continue
        else:
            print(f"✅ > 5 bars and majority flush down, flush down bars: {len(flush_down_bars)}, total bars: {total_bar_count}")

        # Check 6 bars after break below bear trap
        post_break_data = data.loc[date_which_broke_below_bear_trap:].head(6)
        for i, (date, row) in enumerate(post_break_data.iterrows(), 1):
            if row['Close'] > previous_bear_trap[1]:
                print("🚀 All Conditions met!")
                bull_raging_dates.append(date)
                break
            else:
                print(f"❌ check bar {i}, price didn't close above stop loss zone")

    return bull_raging_dates

    # 1. Find bull traps, after which before next bear trap happen
    # a. there is more flush down bars than anything else
    # b. price breaks previous bear trap bear trap
    # c. price CLOSES above stop loss zone within 5 bars after break
    # 2.

    # between previous bull trap and next bull trap should have at MAJORITY flush down bars.
    # majority flush down bar (what is considered majority?) - >50% of bars are flush down bars
    # break through stop loss zone (bear trap)
    # within 5 bars after breakthrough must have bullish bar, closing back into stop loss zone
    # draw mid point between highest and stop loss zone. flush down must start before mid point or touch it
    # enter at bullish bar


@st.cache_data(ttl="1d")
def get_apex_uptrend_dates(data):
    data["SMA_50"] = data["Close"].rolling(window=50).mean()
    data["SMA_200"] = data["Close"].rolling(window=200).mean()

    agg_data = get_2day_aggregated_data(data)

    high_inflexion_points = []
    low_inflexion_points = []
    for i in range(1, len(agg_data) - 1):
        if agg_data["High"][i - 1] < agg_data["High"][i] > agg_data["High"][i + 1]:
            high_inflexion_points.append(agg_data.index[i])
        elif agg_data["Low"][i - 1] > agg_data["Low"][i] < agg_data["Low"][i + 1]:
            low_inflexion_points.append(agg_data.index[i])

    inflexion_points = sorted(high_inflexion_points + low_inflexion_points)
    inflexion_data = agg_data.loc[inflexion_points, ["High", "Low"]]
    inflexion_data = pd.DataFrame(inflexion_data)

    uptrend_dates = []

    # LIGHTNING formation check
    for inflexion_point in high_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 4 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data) - 4:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos + 1]
        point_c = inflexion_data.iloc[inflexion_point_pos + 2]
        point_d = inflexion_data.iloc[inflexion_point_pos + 3]

        # Check for lightning. must start with high inflexion point, C must be lower than A ,   D must be lower than B and cross back to B (assume it just have to reverse in the direction, but havent reach B)
        if point_c["High"] < point_a["High"] and point_d["Low"] < point_b["Low"]:
            # Check if all points are above sma50 and sma200
            if (
                (point_a["Low"] < data.loc[point_a.name, "SMA_50"])
                or (point_a["Low"] < data.loc[point_a.name, "SMA_200"])
                or (point_b["Low"] < data.loc[point_b.name, "SMA_50"])
                or (point_b["Low"] < data.loc[point_b.name, "SMA_200"])
                or (point_c["Low"] < data.loc[point_c.name, "SMA_50"])
                or (point_c["Low"] < data.loc[point_c.name, "SMA_200"])
                or (point_d["Low"] < data.loc[point_d.name, "SMA_50"])
                or (point_d["Low"] < data.loc[point_d.name, "SMA_200"])
            ):
                break

            # add all the dateindex of 4 inflexion points abcd
            uptrend_dates.append(inflexion_data.index[inflexion_point_pos + 3])
            print(
                [
                    "Lightning formation",
                    inflexion_point,
                    inflexion_data.index[inflexion_point_pos + 1],
                    inflexion_data.index[inflexion_point_pos + 2],
                    inflexion_data.index[inflexion_point_pos + 3],
                ]
            )

    # M formation check: D must be higher than  B and cross back to C to reach E (above A)
    for inflexion_point in low_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 5 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data) - 5:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos + 1]
        point_c = inflexion_data.iloc[inflexion_point_pos + 2]
        point_d = inflexion_data.iloc[inflexion_point_pos + 3]
        point_e = inflexion_data.iloc[inflexion_point_pos + 4]

        # Check for M formation. must start with low inflexion point, D must be higher than B, and cross back to C to reach E (above A)
        if (
            point_d["High"] > point_b["High"]
            and point_c["Low"] > point_e["Low"] > point_a["Low"]
        ):
            # Check if all points are above sma50 and sma200
            if (
                (point_a["Low"] < data.loc[point_a.name, "SMA_50"])
                or (point_a["Low"] < data.loc[point_a.name, "SMA_200"])
                or (point_b["Low"] < data.loc[point_b.name, "SMA_50"])
                or (point_b["Low"] < data.loc[point_b.name, "SMA_200"])
                or (point_c["Low"] < data.loc[point_c.name, "SMA_50"])
                or (point_c["Low"] < data.loc[point_c.name, "SMA_200"])
                or (point_d["Low"] < data.loc[point_d.name, "SMA_50"])
                or (point_d["Low"] < data.loc[point_d.name, "SMA_200"])
                or (point_e["Low"] < data.loc[point_e.name, "SMA_50"])
                or (point_e["Low"] < data.loc[point_e.name, "SMA_200"])
            ):
                break
            # add all the dateindex of 4 inflexion points abcd
            uptrend_dates.append(inflexion_data.index[inflexion_point_pos + 3])
            print(
                [
                    "M formation",
                    inflexion_point,
                    inflexion_data.index[inflexion_point_pos + 1],
                    inflexion_data.index[inflexion_point_pos + 2],
                    inflexion_data.index[inflexion_point_pos + 3],
                ]
            )

    return uptrend_dates


@st.cache_data(ttl="1d")
def get_apex_downtrend_dates(data):
    data["SMA_50"] = data["Close"].rolling(window=50).mean()

    agg_data = get_2day_aggregated_data(data)

    high_inflexion_points = []
    low_inflexion_points = []
    for i in range(1, len(agg_data) - 1):
        if agg_data["High"][i - 1] < agg_data["High"][i] > agg_data["High"][i + 1]:
            high_inflexion_points.append(agg_data.index[i])
        elif agg_data["Low"][i - 1] > agg_data["Low"][i] < agg_data["Low"][i + 1]:
            low_inflexion_points.append(agg_data.index[i])

    inflexion_points = sorted(high_inflexion_points + low_inflexion_points)
    inflexion_data = agg_data.loc[inflexion_points, ["High", "Low"]]
    inflexion_data = pd.DataFrame(inflexion_data)

    downtrend_dates = []

    # N formation check
    for inflexion_point in low_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 4 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data) - 4:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos + 1]
        point_c = inflexion_data.iloc[inflexion_point_pos + 2]
        point_d = inflexion_data.iloc[inflexion_point_pos + 3]

        # Check for N. must start with low inflexion point, C must be higher than A , D must be higher than B and cross back to B (assume it just have to reverse in the direction, but havent reach B)
        if point_c["High"] > point_a["High"] and point_d["Low"] > point_b["Low"]:
            # Check if all points are below sma50
            if (
                (point_a["Low"] > data.loc[point_a.name, "SMA_50"])
                or (point_b["Low"] > data.loc[point_b.name, "SMA_50"])
                or (point_c["Low"] > data.loc[point_c.name, "SMA_50"])
                or (point_d["Low"] > data.loc[point_d.name, "SMA_50"])
            ):
                break

            # add all the dateindex of 4 inflexion points abcd
            downtrend_dates.append(inflexion_data.index[inflexion_point_pos + 3])
            print(
                [
                    "N formation",
                    inflexion_point,
                    inflexion_data.index[inflexion_point_pos + 1],
                    inflexion_data.index[inflexion_point_pos + 2],
                    inflexion_data.index[inflexion_point_pos + 3],
                ]
            )

    # W formation check: D must be lower than  B and cross back to C to reach E (below A)
    for inflexion_point in high_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 5 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data) - 5:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos + 1]
        point_c = inflexion_data.iloc[inflexion_point_pos + 2]
        point_d = inflexion_data.iloc[inflexion_point_pos + 3]
        point_e = inflexion_data.iloc[inflexion_point_pos + 4]

        # Check for M formation. must start with low inflexion point, D must be lower than  B and cross back to C to reach E (below A)
        if (
            point_d["Low"] < point_b["Low"]
            and point_c["High"] < point_e["High"] < point_a["High"]
        ):
            # Check if all points are below sma50
            if (
                (point_a["Low"] > data.loc[point_a.name, "SMA_50"])
                or (point_b["Low"] > data.loc[point_b.name, "SMA_50"])
                or (point_c["Low"] > data.loc[point_c.name, "SMA_50"])
                or (point_d["Low"] > data.loc[point_d.name, "SMA_50"])
                or (point_e["Low"] > data.loc[point_e.name, "SMA_50"])
            ):
                break
            # add all the dateindex of 4 inflexion points abcd
            downtrend_dates.append(inflexion_data.index[inflexion_point_pos + 3])
            print(
                [
                    "W formation",
                    inflexion_point,
                    inflexion_data.index[inflexion_point_pos + 1],
                    inflexion_data.index[inflexion_point_pos + 2],
                    inflexion_data.index[inflexion_point_pos + 3],
                ]
            )

    return downtrend_dates


def get_apex_bull_appear_dates(data):
    aggregated_data = get_2day_aggregated_data(data)

    # Find dates where the high of the current day is lower than the high of the previous day = Kangaroo wallaby formation
    condition = (aggregated_data["High"] < aggregated_data["High"].shift(1)) & (
        aggregated_data["Low"] > aggregated_data["Low"].shift(1)
    )
    wallaby_dates = aggregated_data.index[condition]

    bull_appear_dates = []
    potential_bear_traps = get_low_inflexion_points(aggregated_data)
    for date in wallaby_dates:
        print(f"======{date}======")
        wallaby_pos = aggregated_data.index.get_loc(date)
        kangaroo_pos = wallaby_pos - 1

        # Get date index 1 year before date, approximately 126 indexes before
        start_index = max(0, wallaby_pos - 126)
        end_index = kangaroo_pos - 1

        active_bear_traps = find_bear_traps(potential_bear_traps, aggregated_data.index[start_index], aggregated_data.index[end_index])
        if not active_bear_traps:
            continue
        
        any_bar_went_below_kangaroo = False
        bullish_bar_went_back_up_to_range = False
        bear_trap_taken = False
        # Check the next 4 trading dates from wallaby date
        for i in range(1, 5):
            print(f"Checking {i} days after wallaby date")
            target_pos = wallaby_pos + i
            if target_pos >= len(aggregated_data):
                break

            curr_data = aggregated_data.iloc[target_pos]
            curr_date = aggregated_data.index[target_pos]

            # Condition 1: Low below the low of the kangaroo wallaby,
            if (not any_bar_went_below_kangaroo and curr_data["Low"] < aggregated_data.iloc[kangaroo_pos]["Low"]):
                any_bar_went_below_kangaroo = True
                print("Condition 1 met")
            

            # Condition 2: must have one of 3 bullish bars (after going out of K range), close between low and high of kangaroo wallaby
            if any_bar_went_below_kangaroo and not bullish_bar_went_back_up_to_range and aggregated_data.iloc[kangaroo_pos]["Low"] < curr_data["Close"] < aggregated_data.iloc[kangaroo_pos]["High"]:
                print("condition2: close between low and high met")
                if (
                    curr_data["Open"]
                    > curr_data["Low"] + 2 / 3 * (curr_data["High"] - curr_data["Low"])
                    and curr_data["Close"]
                    > curr_data["Low"] + 2 / 3 * (curr_data["High"] - curr_data["Low"])
                ) or curr_data["Close"] - curr_data["Open"] > 0.5 * (
                    curr_data["High"] - curr_data["Low"]
                ):
                    bullish_bar_went_back_up_to_range = True
                    print("Condition 2: bullish bar met")

            # Condition 3: check if there is a bear trap that has not taken the money with price between the low and high of K until today
            
            if not bear_trap_taken and any(
                trap[1] > curr_data["Low"] and trap[1] < curr_data["High"]
                for trap in active_bear_traps
            ):
                bear_trap_taken = True
                print(f"condition3: bear trap met, {active_bear_traps}")

            if any_bar_went_below_kangaroo and bullish_bar_went_back_up_to_range and bear_trap_taken:
                bull_appear_dates.append(curr_date)
                print(
                    "✅ Wallaby date: "
                    + str(date)
                    + "; Bull appear date: "
                    + str(curr_date)
                )
                break
                    
        

    return pd.DatetimeIndex(bull_appear_dates)


@st.cache_data(ttl="1d")
def get_apex_bear_appear_dates(data):
    aggregated_data = get_2day_aggregated_data(data)
    # TODO: implement after bull appear is confirmed to be working because similar logic
    return []


def get_golden_cross_sma_dates(data, short_window=50, long_window=200):
    data[f"SMA_{short_window}"] = data["Close"].rolling(window=short_window).mean()
    data[f"SMA_{long_window}"] = data["Close"].rolling(window=long_window).mean()
    data[f"Prev_SMA_{short_window}"] = data[f"SMA_{short_window}"].shift(1)
    data[f"Prev_SMA_{long_window}"] = data[f"SMA_{long_window}"].shift(1)

    golden_cross = (data[f"SMA_{short_window}"] > data[f"SMA_{long_window}"]) & (
        data[f"Prev_SMA_{short_window}"] <= data[f"Prev_SMA_{long_window}"]
    )

    golden_cross_dates = golden_cross[golden_cross].index
    return golden_cross_dates


def get_death_cross_sma_dates(data, short_window=50, long_window=200):
    data[f"SMA_{short_window}"] = data["Close"].rolling(window=short_window).mean()
    data[f"SMA_{long_window}"] = data["Close"].rolling(window=long_window).mean()
    data[f"Prev_SMA_{short_window}"] = data[f"SMA_{short_window}"].shift(1)
    data[f"Prev_SMA_{long_window}"] = data[f"SMA_{long_window}"].shift(1)

    death_cross = (data[f"SMA_{short_window}"] < data[f"SMA_{long_window}"]) & (
        data[f"Prev_SMA_{short_window}"] >= data[f"Prev_SMA_{long_window}"]
    )
    death_cross_dates = death_cross[death_cross].index

    return death_cross_dates


def get_rsi_overbought_dates(data, threshold=70):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))
    if data["RSI"].empty:
        return False
    overbought = data["RSI"] > threshold
    overbought_dates = overbought[overbought].index

    return overbought_dates


def get_rsi_oversold_dates(data, threshold=30):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    oversold = data["RSI"] < threshold
    oversold_dates = oversold[oversold].index
    return oversold_dates


def get_macd_bullish_dates(data, short_window=12, long_window=26, signal_window=9):
    data["Short_EMA"] = data["Close"].ewm(span=short_window, adjust=False).mean()
    data["Long_EMA"] = data["Close"].ewm(span=long_window, adjust=False).mean()
    data["MACD"] = data["Short_EMA"] - data["Long_EMA"]
    data["Signal_Line"] = data["MACD"].ewm(span=signal_window, adjust=False).mean()

    bullish = (data["MACD"] > data["Signal_Line"]) & (
        data["MACD"].shift(1) <= data["Signal_Line"].shift(1)
    )
    bullish_dates = bullish[bullish].index
    return bullish_dates


def get_macd_bearish_dates(data, short_window=12, long_window=26, signal_window=9):
    data["Short_EMA"] = data["Close"].ewm(span=short_window, adjust=False).mean()
    data["Long_EMA"] = data["Close"].ewm(span=long_window, adjust=False).mean()
    data["MACD"] = data["Short_EMA"] - data["Long_EMA"]
    data["Signal_Line"] = data["MACD"].ewm(span=signal_window, adjust=False).mean()

    bearish = (data["MACD"] < data["Signal_Line"]) & (
        data["MACD"].shift(1) >= data["Signal_Line"].shift(1)
    )
    bearish_dates = bearish[bearish].index
    return bearish_dates


def get_bollinger_band_squeeze_dates(data, window=20, num_std_dev=2):
    data["Middle_Band"] = data["Close"].rolling(window=window).mean()
    data["Upper_Band"] = (
        data["Middle_Band"] + num_std_dev * data["Close"].rolling(window=window).std()
    )
    data["Lower_Band"] = (
        data["Middle_Band"] - num_std_dev * data["Close"].rolling(window=window).std()
    )

    squeeze = (data["Upper_Band"] - data["Lower_Band"]) / data["Middle_Band"] <= 0.05
    squeeze_dates = squeeze[squeeze].index
    return squeeze_dates


def get_bollinger_band_expansion_dates(data, window=20, num_std_dev=2):
    data["Middle_Band"] = data["Close"].rolling(window=window).mean()
    data["Upper_Band"] = (
        data["Middle_Band"] + num_std_dev * data["Close"].rolling(window=window).std()
    )
    data["Lower_Band"] = (
        data["Middle_Band"] - num_std_dev * data["Close"].rolling(window=window).std()
    )

    expansion = (data["Upper_Band"] - data["Lower_Band"]) / data["Middle_Band"] >= 0.1
    expansion_dates = expansion[expansion].index
    return expansion_dates


def get_bollinger_band_breakout_dates(data, window=20, num_std_dev=2):
    data["Middle_Band"] = data["Close"].rolling(window=window).mean()
    data["Upper_Band"] = (
        data["Middle_Band"] + num_std_dev * data["Close"].rolling(window=window).std()
    )
    data["Lower_Band"] = (
        data["Middle_Band"] - num_std_dev * data["Close"].rolling(window=window).std()
    )

    breakout = data["Close"] > data["Upper_Band"]
    breakout_dates = breakout[breakout].index
    return breakout_dates


def get_bollinger_band_pullback_dates(data, window=20, num_std_dev=2):
    data["Middle_Band"] = data["Close"].rolling(window=window).mean()
    data["Upper_Band"] = (
        data["Middle_Band"] + num_std_dev * data["Close"].rolling(window=window).std()
    )
    data["Lower_Band"] = (
        data["Middle_Band"] - num_std_dev * data["Close"].rolling(window=window).std()
    )

    pullback = data["Close"] < data["Lower_Band"]
    pullback_dates = pullback[pullback].index
    return pullback_dates


def get_volume_spike_dates(data, window=20, num_std_dev=2):
    data["Volume_MA"] = data["Volume"].rolling(window=window).mean()
    data["Volume_MA_std"] = data["Volume"].rolling(window=window).std()

    spike = data["Volume"] > data["Volume_MA"] + num_std_dev * data["Volume_MA_std"]
    spike_dates = spike[spike].index
    return spike_dates
