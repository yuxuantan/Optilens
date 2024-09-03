import yfinance as yf
import pandas as pd
from typing import List, Dict
import streamlit as st

@st.cache_data(ttl="1d")
def fetch_stock_data(ticker, period='max', interval='1d') -> pd.DataFrame:
    try:
        data = yf.download(ticker, period=period, interval=interval)
        return data
    except Exception as e:
        print(f"Failed to fetch data for {ticker}")
        return None

def analyze_stock(ticker: str, settings: Dict[str, int]) -> List[str]:
    """Analyze a stock and return notifications based on user preferences."""
    
    data = fetch_stock_data(ticker, period='max', interval='1d')
    
    # Filter out indicator settings with is_enabled = False
    enabled_settings = {k: v for k, v in settings["indicator_settings"].items() if v["is_enabled"]}
    
    # Store dates where each indicator's condition is met
    indicator_dates = {}

    # Check enabled indicators and get the dates where the condition is met
    for indicator, config in enabled_settings.items():
        dates = None
        if indicator == "golden_cross_sma":
            dates = get_golden_cross_sma_dates(ticker, data, config["short_sma"], config["long_sma"])
        elif indicator == "death_cross_sma":
            dates = get_death_cross_sma_dates(ticker, data, config["short_sma"], config["long_sma"])
        elif indicator == "rsi_overbought":
            dates = get_rsi_overbought_dates(ticker, data, config["threshold"])
        elif indicator == "rsi_oversold":
            dates = get_rsi_oversold_dates(ticker, data, config["threshold"])
        elif indicator == "macd_bullish":
            dates = get_macd_bullish_dates(ticker, data, config["short_ema"], config["long_ema"], config["signal_window"])
        elif indicator == "macd_bearish":
            dates = get_macd_bearish_dates(ticker, data, config["short_ema"], config["long_ema"], config["signal_window"])
        elif indicator == "bollinger_squeeze":
            dates = get_bollinger_band_squeeze_dates(ticker, data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_expansion":
            dates = get_bollinger_band_expansion_dates(ticker, data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_breakout":
            dates = get_bollinger_band_breakout_dates(ticker, data, config["window"], config["num_std_dev"])
        elif indicator == "bollinger_pullback":
            dates = get_bollinger_band_pullback_dates(ticker, data, config["window"], config["num_std_dev"])
        elif indicator == "volume_spike":
            dates = get_volume_spike_dates(ticker, data, config["window"], config["num_std_dev"])
        
        # if the latest date does not exist in the data, return None
        if dates is None or len(dates)==0 or (dates[-1] != data.index[-1]):
            return None
        
        indicator_dates[indicator] = dates
    
    
    # Find common dates between all enabled indicators
    common_dates = set(data.index)
    for dates in indicator_dates.values():
        common_dates.intersection_update(dates)
    
    common_dates = sorted(common_dates)  # Sort dates for clarity

    # Calculate the success rate based on provided logic
    success_count = 0
    for date in common_dates:
        if (date + pd.Timedelta(days=settings["x"])) in data.index and data.loc[date + pd.Timedelta(days=settings["x"]), 'Close'] > data.loc[date, 'Close']:
            success_count += 1

    total_instances = len(common_dates)
    success_rate = (success_count / total_instances * 100) if total_instances > 0 else 0

   # Calculate the average percentage change
    avg_percentage_change = 0
    valid_count = 0  # To keep track of how many valid instances we have

    for date in common_dates:
        future_date = date + pd.Timedelta(days=settings["x"])
        
        if date in data.index and future_date in data.index:
            try:
                current_close = data.loc[date, 'Close']
                future_close = data.loc[future_date, 'Close']
                percentage_change = (future_close - current_close) / current_close * 100
                avg_percentage_change += percentage_change
                valid_count += 1
            except KeyError:
                # Handle the case where 'Close' might not be in the DataFrame (unlikely but for completeness)
                print(f"Missing 'Close' price for date: {date} or {future_date}")
        else:
            print(f"Date {date} or {future_date} is not in the DataFrame")

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



def get_golden_cross_sma_dates(ticker, data=None, short_window=50, long_window=200):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')

    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    data[f'Prev_SMA_{short_window}'] = data[f'SMA_{short_window}'].shift(1)
    data[f'Prev_SMA_{long_window}'] = data[f'SMA_{long_window}'].shift(1)

    golden_cross = (data[f'SMA_{short_window}'] > data[f'SMA_{long_window}']) & (data[f'Prev_SMA_{short_window}'] <= data[f'Prev_SMA_{long_window}'])

    golden_cross_dates = golden_cross[golden_cross].index
    return golden_cross_dates


def get_death_cross_sma_dates(ticker, data=None, short_window=50, long_window=200):
    if data is None:
        try:
            data = yf.download(ticker, period='1y', interval='1d')
        except:
            data = yf.download(ticker, period='max', interval='1d')
    
    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    data[f'Prev_SMA_{short_window}'] = data[f'SMA_{short_window}'].shift(1)
    data[f'Prev_SMA_{long_window}'] = data[f'SMA_{long_window}'].shift(1)
    
    death_cross = (data[f'SMA_{short_window}'] < data[f'SMA_{long_window}']) & (data[f'Prev_SMA_{short_window}'] >= data[f'Prev_SMA_{long_window}'])
    death_cross_dates = death_cross[death_cross].index

    return death_cross_dates
    

def get_rsi_overbought_dates(ticker, data=None, threshold=70):
    if data is None:
        try:
            data = yf.download(ticker, period='1y', interval='1d')
        except:
            data = yf.download(ticker, period='max', interval='1d')
    
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

def get_rsi_oversold_dates(ticker, data=None, threshold=30):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
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


def get_macd_bullish_dates(ticker, data=None, short_window=12, long_window=26, signal_window=9):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Short_EMA'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['Long_EMA'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['Short_EMA'] - data['Long_EMA']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    bullish = (data['MACD'] > data['Signal_Line']) & (data['MACD'].shift(1) <= data['Signal_Line'].shift(1))
    bullish_dates = bullish[bullish].index
    return bullish_dates

def get_macd_bearish_dates(ticker, data=None, short_window=12, long_window=26, signal_window=9):
    if data is None:
        try:
            data = yf.download(ticker, period='1y', interval='1d')
        except:
            data = yf.download(ticker, period='max', interval='1d')
    
    data['Short_EMA'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['Long_EMA'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['Short_EMA'] - data['Long_EMA']
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    
    bearish = (data['MACD'] < data['Signal_Line']) & (data['MACD'].shift(1) >= data['Signal_Line'].shift(1))
    bearish_dates = bearish[bearish].index
    return bearish_dates

def get_bollinger_band_squeeze_dates(ticker, data=None, window=20, num_std_dev=2):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    squeeze = (data['Upper_Band'] - data['Lower_Band']) / data['Middle_Band'] <= 0.05
    squeeze_dates = squeeze[squeeze].index
    return squeeze_dates

def get_bollinger_band_expansion_dates(ticker, data=None, window=20, num_std_dev=2):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    expansion = (data['Upper_Band'] - data['Lower_Band']) / data['Middle_Band'] >= 0.1
    expansion_dates = expansion[expansion].index
    return expansion_dates

def get_bollinger_band_breakout_dates(ticker, data=None, window=20, num_std_dev=2):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    breakout = data['Close'] > data['Upper_Band']
    breakout_dates = breakout[breakout].index
    return breakout_dates

def get_bollinger_band_pullback_dates(ticker, data=None, window=20, num_std_dev=2):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Middle_Band'] = data['Close'].rolling(window=window).mean()
    data['Upper_Band'] = data['Middle_Band'] + num_std_dev * data['Close'].rolling(window=window).std()
    data['Lower_Band'] = data['Middle_Band'] - num_std_dev * data['Close'].rolling(window=window).std()
    
    pullback = data['Close'] < data['Lower_Band']
    pullback_dates = pullback[pullback].index
    return pullback_dates

def get_volume_spike_dates(ticker, data=None, window=20, num_std_dev=2):
    if data is None:
        data = yf.download(ticker, period='max', interval='1d')
    
    data['Volume_MA'] = data['Volume'].rolling(window=window).mean()
    data['Volume_MA_std'] = data['Volume'].rolling(window=window).std()
    
    spike = data['Volume'] > data['Volume_MA'] + num_std_dev * data['Volume_MA_std']
    spike_dates = spike[spike].index
    return spike_dates
