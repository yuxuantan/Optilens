import pandas as pd
from typing import List, Dict
import streamlit as st
from datetime import datetime
import utils.ticker_getter as tg


def analyze_stock(ticker: str, settings: Dict[str, int]) -> List[str]:
    """Analyze a stock and return notifications based on user preferences."""
    print(ticker)
    data = tg.fetch_stock_data(ticker, period='max', interval='1d')
    
    # Filter out indicator settings with is_enabled = False
    enabled_settings = {k: v for k, v in settings["indicator_settings"].items() if v["is_enabled"]}
    
    # Store dates where each indicator's condition is met
    indicator_dates = {}

    # get the date x trading days before last day in stock data
    recency_cutoff_date = None
    if len(data.index) > 0:
        recency_cutoff_date = data.index[-min(settings["recency"], len(data.index)-1)]

    # Check enabled indicators and get the dates where the condition is met
    for indicator, config in enabled_settings.items():
        dates = None
        if indicator == "golden_cross_sma":
            dates = get_golden_cross_sma_dates(data, config["short_sma"], config["long_sma"])
        elif indicator == "death_cross_sma":
            dates = get_death_cross_sma_dates(data, config["short_sma"], config["long_sma"])
        elif indicator == "rsi_overbought":
            dates = get_rsi_overbought_dates(data, config["threshold"])
        elif indicator == "rsi_oversold":
            dates = get_rsi_oversold_dates(data, config["threshold"])
        elif indicator == "macd_bullish":
            dates = get_macd_bullish_dates(data, config["short_ema"], config["long_ema"], config["signal_window"])
        elif indicator == "macd_bearish":
            dates = get_macd_bearish_dates(data, config["short_ema"], config["long_ema"], config["signal_window"])
        elif indicator == "bollinger_squeeze":
            dates = get_bollinger_band_squeeze_dates(data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_expansion":
            dates = get_bollinger_band_expansion_dates(data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_breakout":
            dates = get_bollinger_band_breakout_dates(data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_pullback":
            dates = get_bollinger_band_pullback_dates(data, config["window"], config["num_std_dev"])
        elif indicator == "volume_spike":
            dates = get_volume_spike_dates(data, config["window"], config["num_std_dev"])
        elif indicator == "apex_bull_appear":
            dates = get_apex_bull_appear_dates(data)
        elif indicator == "apex_bear_appear":
            dates = get_apex_bear_appear_dates(data)
        elif indicator == "apex_uptrend":
            dates = get_uptrend_formation_dates(data)
        
        # If no dates are found, skip this indicator
        if dates is None or len(dates)==0:
            return None
        
        ## if the latest date does not exist in the data, return None
        # if (dates[-1] != data.index[-1]):
        #     return None

        # last indicator appear date
        last_date_detected = dates[-1]
        
        # check the last x dates using index
        if (last_date_detected < recency_cutoff_date):
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
        if (target_date_for_metric_calculation) in data.index and data.loc[target_date_for_metric_calculation, 'Close'] > data.loc[date, 'Close']:
            success_count += 1
        
        # Calculate the average percentage change
        if date in data.index and target_date_for_metric_calculation in data.index:
            try:
                current_close = data.loc[date, 'Close']
                future_close = data.loc[target_date_for_metric_calculation, 'Close']
                percentage_change = (future_close - current_close) / current_close * 100
                avg_percentage_change += percentage_change
                valid_count += 1
            except KeyError:
                # Handle the case where 'Close' might not be in the DataFrame (unlikely but for completeness)
                print(f"Missing 'Close' price for date: {date} or {target_date_for_metric_calculation}")
        else:
            print(f"Date {date} or {target_date_for_metric_calculation} is not in the DataFrame")

    total_instances = len(common_dates)
    success_rate = (success_count / total_instances * 100) if total_instances > 0 else 0
        
    # Calculate the average percentage change if there are valid instances
    avg_percentage_change = avg_percentage_change / valid_count if valid_count > 0 else 0

    # Compile results
    result = {
        "common_dates": [str(date) for date in common_dates],
        "total_instances": total_instances,
        "success_rate": success_rate,
        "avg_percentage_change": avg_percentage_change
    }

    return result


def get_2day_aggregated_data(data):
    # Ensure the Date column is the index and is of datetime type
    data.index = pd.to_datetime(data.index)

    # if there is odd number of data points, drop the first row in the aggregate calculation
    if len(data) % 2 == 1:
        data = data.iloc[1:]

    # Group data into 2-day periods of price movement (2-day chart)
    grouped = data[['High', 'Low', 'Open', 'Close']].rolling(window=2, min_periods=1).agg({
        'High': 'max',
        'Low': 'min',
        'Open': lambda x: x.iloc[0],
        'Close': lambda x: x.iloc[-1]
    })
    aggregated_data = grouped.shift(-1).iloc[::2]
    return aggregated_data


def get_bear_traps(data):
    # get all bear trap dates and values = u or v shape, where T-1 low > T low < T+1 low. Identify T
    
    bear_trap_dates = []
    for i in range(1, len(data)-1):
        if data['Low'][i-1] > data['Low'][i] and data['Low'][i] < data['Low'][i+1]:
            bear_trap_dates.append(data.index[i])
    
    # get bear traps that are still valid. 
    return bear_trap_dates
    # if no bear trap



@st.cache_data(ttl="1d")
def get_uptrend_formation_dates(data):
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()

    agg_data = get_2day_aggregated_data(data)

    high_inflexion_points = []
    low_inflexion_points = []
    for i in range(1, len(agg_data)-1):
        if (agg_data['High'][i-1] < agg_data['High'][i] > agg_data['High'][i+1]):
            high_inflexion_points.append(agg_data.index[i])
        elif (agg_data['Low'][i-1] > agg_data['Low'][i] < agg_data['Low'][i+1]):
            low_inflexion_points.append(agg_data.index[i])

    inflexion_points = sorted(high_inflexion_points + low_inflexion_points)
    inflexion_data = agg_data.loc[inflexion_points, ['High', 'Low']]
    inflexion_data = pd.DataFrame(inflexion_data)

    
    uptrend_dates = []

    # TODO: Note that uptrend formation must form above sma50 line & sma200. 

    # LIGHTNING formation check
    for inflexion_point in high_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 4 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data)-4:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos+1]
        point_c = inflexion_data.iloc[inflexion_point_pos+2]
        point_d = inflexion_data.iloc[inflexion_point_pos+3]

        # Check for lightning. must start with high inflexion point, C must be lower than A ,   D must be lower than B and cross back to B (assume it just have to reverse in the direction, but havent reach B)
        if point_c['High'] < point_a['High'] and point_d['Low'] < point_b['Low']:
            # Check if all points are above sma50 and sma200
            if(point_a['Low'] < data.loc[point_a.name, 'SMA_50']) or (point_a['Low'] < data.loc[point_a.name, 'SMA_200']) or (point_b['Low'] < data.loc[point_b.name, 'SMA_50']) or (point_b['Low'] < data.loc[point_b.name, 'SMA_200']) or (point_c['Low'] < data.loc[point_c.name, 'SMA_50']) or (point_c['Low'] < data.loc[point_c.name, 'SMA_200']) or (point_d['Low'] < data.loc[point_d.name, 'SMA_50']) or (point_d['Low'] < data.loc[point_d.name, 'SMA_200']):
                break

            # add all the dateindex of 4 inflexion points abcd
            uptrend_dates.append(inflexion_data.index[inflexion_point_pos+3])
            print(['Lightning formation', inflexion_point, inflexion_data.index[inflexion_point_pos+1], inflexion_data.index[inflexion_point_pos+2], inflexion_data.index[inflexion_point_pos+3]])

    # M formation check: D must be higher than  B and cross back to C to reach E (above A)
    for inflexion_point in low_inflexion_points:
        # get index of inflexion point
        inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
        # if inflexion point is one of the last 5 datapoints, skip
        if inflexion_point_pos >= len(inflexion_data)-5:
            break

        # Get price of first inflexion point
        point_a = inflexion_data.iloc[inflexion_point_pos]
        point_b = inflexion_data.iloc[inflexion_point_pos+1]
        point_c = inflexion_data.iloc[inflexion_point_pos+2]
        point_d = inflexion_data.iloc[inflexion_point_pos+3]
        point_e = inflexion_data.iloc[inflexion_point_pos+4]
        

        # Check for M formation. must start with low inflexion point, D must be higher than B, and cross back to C to reach E (above A)
        if point_d['High'] > point_b['High'] and point_c['Low'] > point_e['Low'] > point_a['Low'] :
            # Check if all points are above sma50 and sma200
            if(point_a['Low'] < data.loc[point_a.name, 'SMA_50']) or (point_a['Low'] < data.loc[point_a.name, 'SMA_200']) or (point_b['Low'] < data.loc[point_b.name, 'SMA_50']) or (point_b['Low'] < data.loc[point_b.name, 'SMA_200']) or (point_c['Low'] < data.loc[point_c.name, 'SMA_50']) or (point_c['Low'] < data.loc[point_c.name, 'SMA_200']) or (point_d['Low'] < data.loc[point_d.name, 'SMA_50']) or (point_d['Low'] < data.loc[point_d.name, 'SMA_200']) or (point_e['Low'] < data.loc[point_e.name, 'SMA_50']) or (point_e['Low'] < data.loc[point_e.name, 'SMA_200']):
                break
            # add all the dateindex of 4 inflexion points abcd
            uptrend_dates.append(inflexion_data.index[inflexion_point_pos+3])
            print(['M formation',inflexion_point, inflexion_data.index[inflexion_point_pos+1], inflexion_data.index[inflexion_point_pos+2], inflexion_data.index[inflexion_point_pos+3]])


    return uptrend_dates

    
if __name__ =="__main__":
    get_uptrend_formation_dates()

@st.cache_data(ttl="1d")
def get_apex_bull_appear_dates(data):
    
    aggregated_data = get_2day_aggregated_data(data)

    # Find dates where the high of the current day is lower than the high of the previous day = Kangaroo wallaby formation
    condition = (aggregated_data['High'] < aggregated_data['High'].shift(1)) & (aggregated_data['Low'] > aggregated_data['Low'].shift(1))
    wallaby_dates = aggregated_data.index[condition]
    print("wallaby_dates: "+str(wallaby_dates))
    # if last wallaby date is more than 7 days ago, return None to cut the processing time because bull appear cannot be today
    if len(wallaby_dates) > 0 and (datetime.now() - wallaby_dates[-1].to_pydatetime()).days > 7:
        return None
    
    # TODO: check the MIN price of bear trap that has not taken the money yet. it has to be between the low and high of the kangaroo

    bull_appear_dates = []
    for date in wallaby_dates:
        # Check the next 4 trading dates from wallaby date
        for i in range(1, 5):
            # get the data for this date, using index to get the data
            wallaby_pos = aggregated_data.index.get_loc(date)
            kangaroo_pos = wallaby_pos - 1
            target_pos = wallaby_pos + i
            # Ensure the target position is within the DataFrame bounds
            if target_pos >= len(aggregated_data):
                break
            
            curr_data = aggregated_data.iloc[target_pos]
            curr_date = aggregated_data.index[target_pos]

            # condition1: low below the low of the kangaroo wallaby, close between the low and high of the kangaroo
            if curr_data['Low'] < aggregated_data.iloc[kangaroo_pos]['Low'] and curr_data['Close'] > aggregated_data.iloc[kangaroo_pos]['Low'] and curr_data['Close'] < aggregated_data.iloc[kangaroo_pos]['High']:

                # condition2: must be one of 3 bullish bar
                # check for bullish pin (open and close both at top 1/3 of bar) # check for bullish ice cream OR bullish flush up (open and close gap is >50% of high and low gap, and close > open)
                if (
                    (curr_data['Open']> curr_data['Low'] + 2/3*(curr_data['High'] - curr_data['Low']) and curr_data['Close']> curr_data['Low'] + 2/3*(curr_data['High'] - curr_data['Low']))) or curr_data['Close'] - curr_data['Open'] > 0.5*(curr_data['High'] - curr_data['Low']):
                    bull_appear_dates.append(curr_date)
                    print(f"Wallaby date: {date}; Bull appear date: {curr_date}")

    
    # return bull_appear_dates
    return pd.DatetimeIndex(bull_appear_dates)
    
@st.cache_data(ttl="1d")
def get_apex_bear_appear_dates(data):
    
    aggregated_data = get_2day_aggregated_data(data)

    # Find dates where the high of the current day is lower than the high of the previous day = Kangaroo wallaby formation
    condition = (aggregated_data['High'] < aggregated_data['High'].shift(1)) & (aggregated_data['Low'] > aggregated_data['Low'].shift(1))
    wallaby_dates = aggregated_data.index[condition]
    print("wallaby_dates: "+str(wallaby_dates))
    # if last wallaby date is more than 7 days ago, return None to cut the processing time because bull appear cannot be today
    if len(wallaby_dates) > 0 and (datetime.now() - wallaby_dates[-1].to_pydatetime()).days > 7:
        return None
    
    # TODO: check the MIN price of bull trap that has not taken the money yet. it has to be between the low and high of the kangaroo

    bear_appear_dates = []
    for date in wallaby_dates:
        # Check the next 4 trading dates from wallaby date
        for i in range(1, 5):
            # get the data for this date, using index to get the data
            wallaby_pos = aggregated_data.index.get_loc(date)
            kangaroo_pos = wallaby_pos - 1
            target_pos = wallaby_pos + i
            # Ensure the target position is within the DataFrame bounds
            if target_pos >= len(aggregated_data):
                break
            
            curr_data = aggregated_data.iloc[target_pos]
            curr_date = aggregated_data.index[target_pos]

            # condition1: high above the high of the kangaroo wallaby, close between the low and high of the kangaroo
            if curr_data['High'] > aggregated_data.iloc[kangaroo_pos]['High'] and curr_data['Close'] > aggregated_data.iloc[kangaroo_pos]['Low'] and curr_data['Close'] < aggregated_data.iloc[kangaroo_pos]['High']:

                # condition2: must be one of 3 bearish bar
                # check for bearish pin (open and close both at bottom 1/3 of bar) # check for bearish ice cream OR bearish flush down (open and close gap is >50% of high and low gap, and open > close)
                if (
                    (curr_data['Open']> curr_data['Low'] + 1/3*(curr_data['High'] - curr_data['Low']) and curr_data['Close']> curr_data['Low'] + 1/3*(curr_data['High'] - curr_data['Low']))) or curr_data['Open'] - curr_data['Close'] > 0.5*(curr_data['High'] - curr_data['Low']):
                    bear_appear_dates.append(curr_date)
                    print(f"Wallaby date: {date}; Bear appear date: {curr_date}")

    
    # return bull_appear_dates
    return pd.DatetimeIndex(bear_appear_dates)


def get_golden_cross_sma_dates(data, short_window=50, long_window=200):

    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    data[f'Prev_SMA_{short_window}'] = data[f'SMA_{short_window}'].shift(1)
    data[f'Prev_SMA_{long_window}'] = data[f'SMA_{long_window}'].shift(1)

    golden_cross = (data[f'SMA_{short_window}'] > data[f'SMA_{long_window}']) & (data[f'Prev_SMA_{short_window}'] <= data[f'Prev_SMA_{long_window}'])

    golden_cross_dates = golden_cross[golden_cross].index
    return golden_cross_dates


    
def get_death_cross_sma_dates(data, short_window=50, long_window=200):
    
    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    data[f'Prev_SMA_{short_window}'] = data[f'SMA_{short_window}'].shift(1)
    data[f'Prev_SMA_{long_window}'] = data[f'SMA_{long_window}'].shift(1)
    
    death_cross = (data[f'SMA_{short_window}'] < data[f'SMA_{long_window}']) & (data[f'Prev_SMA_{short_window}'] >= data[f'Prev_SMA_{long_window}'])
    death_cross_dates = death_cross[death_cross].index

    return death_cross_dates
    

def get_rsi_overbought_dates(data, threshold=70):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    if data['RSI'].empty:
        return False
    overbought = data['RSI'] > threshold
    overbought_dates = overbought[overbought].index

    return overbought_dates

def get_rsi_oversold_dates(data, threshold=30):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    oversold = data['RSI'] < threshold
    oversold_dates = oversold[oversold].index
    return oversold_dates


def get_macd_bullish_dates(data, short_window=12, long_window=26, signal_window=9):
    data['Short_EMA'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['Long_EMA'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['Short_EMA'] - data['Long_EMA']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    bullish = (data['MACD'] > data['Signal_Line']) & (data['MACD'].shift(1) <= data['Signal_Line'].shift(1))
    bullish_dates = bullish[bullish].index
    return bullish_dates

def get_macd_bearish_dates(data, short_window=12, long_window=26, signal_window=9):
    data['Short_EMA'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['Long_EMA'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['Short_EMA'] - data['Long_EMA']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    bearish = (data['MACD'] < data['Signal_Line']) & (data['MACD'].shift(1) >= data['Signal_Line'].shift(1))
    bearish_dates = bearish[bearish].index
    return bearish_dates

def get_bollinger_band_squeeze_dates(data, window=20, num_std_dev=2):
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    squeeze = (data['Upper_Band'] - data['Lower_Band']) / data['Middle_Band'] <= 0.05
    squeeze_dates = squeeze[squeeze].index
    return squeeze_dates

def get_bollinger_band_expansion_dates(data, window=20, num_std_dev=2):
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    expansion = (data['Upper_Band'] - data['Lower_Band']) / data['Middle_Band'] >= 0.1
    expansion_dates = expansion[expansion].index
    return expansion_dates

def get_bollinger_band_breakout_dates(data, window=20, num_std_dev=2):
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    breakout = data['Close'] > data['Upper_Band']
    breakout_dates = breakout[breakout].index
    return breakout_dates

def get_bollinger_band_pullback_dates(data, window=20, num_std_dev=2):
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    pullback = data['Close'] < data['Lower_Band']
    pullback_dates = pullback[pullback].index
    return pullback_dates

def get_volume_spike_dates(data, window=20, num_std_dev=2):
    data['Volume_MA'] = data['Volume'].rolling(window=window).mean()
    data['Volume_MA_std'] = data['Volume'].rolling(window=window).std()
    
    spike = data['Volume'] > data['Volume_MA'] + num_std_dev * data['Volume_MA_std']
    spike_dates = spike[spike].index
    return spike_dates
