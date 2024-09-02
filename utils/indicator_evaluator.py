import yfinance as yf

from typing import List, Dict

def analyze_stock(ticker: str, settings: Dict[str, int]) -> List[str]:
    
    """Analyze a stock and return notifications based on user preferences."""
    data = yf.download(ticker, period='1y', interval='1d')
    
    
    conditions_met = []
    for indicator_name in settings["indicator_settings"]:
        if settings["indicator_settings"][indicator_name]["is_enabled"] and detect_indicator(indicator_name, settings["indicator_settings"][indicator_name], ticker, data):
            conditions_met.append((ticker, indicator_name, settings["indicator_settings"][indicator_name]))
    
    if settings["include_only_if_all_conditions_satisfied"] and len(conditions_met) != len(list(k for k,v in settings["indicator_settings"].items() if v["is_enabled"])):
        return []

    return conditions_met

def detect_indicator(indicator_name, indicator_settings, ticker, data):
    """
    Detects the indicator based on the configuration provided in indicator_settings.
    """
    if indicator_name == 'golden_cross':
        return detect_golden_cross_sma(ticker, data, short_window=indicator_settings['short_sma'], long_window=indicator_settings['long_sma'], filter_window_days=indicator_settings['filter_window_days'])
    
    if indicator_name == 'death_cross':
        return detect_death_cross_sma(ticker, data, short_window=indicator_settings['short_sma'], long_window=indicator_settings['long_sma'], filter_window_days=indicator_settings['filter_window_days'])
    
    if indicator_name == 'rsi_oversold':
        return detect_rsi_oversold(ticker, data, threshold=indicator_settings['threshold'])
    
    if indicator_name == 'rsi_overbought':
        return detect_rsi_overbought(ticker, data, threshold=indicator_settings['threshold'])
    
    if indicator_name == 'sma_bull_trend':
        return check_if_sma_short_window_is_above_long_window(ticker, short_window=indicator_settings['short_sma'], long_window=indicator_settings['long_sma'], data=data)
    
    if indicator_name == 'sma_bear_trend':
        return not check_if_sma_short_window_is_above_long_window(ticker, short_window=indicator_settings['short_sma'], long_window=indicator_settings['long_sma'], data=data)

    return False


def detect_golden_cross_sma(ticker, data=None, short_window=50, long_window=200, filter_window_days=2):
    if data is None:
        try:
            data = yf.download(ticker, period='1y', interval='1d')
        except:
            data = yf.download(ticker, period='max', interval='1d')
    
    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    data[f'Prev_SMA_{short_window}'] = data[f'SMA_{short_window}'].shift(1)
    data[f'Prev_SMA_{long_window}'] = data[f'SMA_{long_window}'].shift(1)
    
    golden_cross = (data[f'SMA_{short_window}'] > data[f'SMA_{long_window}']) & (data[f'Prev_SMA_{short_window}'] <= data[f'Prev_SMA_{long_window}'])
    
    if golden_cross.empty:
        return False

    if golden_cross.iloc[-filter_window_days:].any():
        return True

    return False

def detect_death_cross_sma(ticker, data=None, short_window=50, long_window=200, filter_window_days=2):
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
    if death_cross.empty:
        return False
    
    if death_cross.iloc[-filter_window_days:].any():
        return True
    
    return False
    

def detect_rsi_overbought(ticker, data=None, threshold=70):
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
    return data['RSI'].iloc[-1] > threshold

def detect_rsi_oversold(ticker, data=None, threshold=30):
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
    return data['RSI'].iloc[-1] < threshold


def check_if_sma_short_window_is_above_long_window(ticker, short_window=50, long_window=200, data=None):
    if data is None:
        try:
            data = yf.download(ticker, period='1y', interval='1d')
        except:
            data = yf.download(ticker, period='max', interval='1d')
    
    data[f'SMA_{short_window}'] = data['Close'].rolling(window=short_window).mean()
    data[f'SMA_{long_window}'] = data['Close'].rolling(window=long_window).mean()
    
    if data[f'SMA_{short_window}'].empty or data[f'SMA_{long_window}'].empty:
        return False
    # Return True if short_window SMA is above long_window SMA, False otherwise
    return data[f'SMA_{short_window}'].iloc[-1] > data[f'SMA_{long_window}'].iloc[-1]