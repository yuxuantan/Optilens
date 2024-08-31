import yfinance as yf
import pandas as pd
import streamlit as st

from typing import List, Dict, Any, Optional

Ticker = str
AlertName = str
AlertSettings = Dict[str, Any]

def analyze_stock(ticker: Ticker, settings: Dict[str, int]) -> List[str]:
    """Analyze a stock and return notifications based on user preferences."""
    data = yf.download(ticker, period='1y', interval='1d')
    notifications = []
    
    preferences = settings['preferences']
    if settings['include_only_if_all_conditions_satisfied']:
        conditions_met = []
        
        if preferences['golden_cross']:
            if detect_golden_cross_sma(ticker, data, short_window=settings['short_sma_golden'], long_window=settings['long_sma_golden']):
                conditions_met.append('golden_cross')
        
        if preferences['death_cross']:
            if detect_death_cross_sma(ticker, data, short_window=settings['short_sma_death'], long_window=settings['long_sma_death']):
                conditions_met.append('death_cross')
        
        if preferences['rsi_oversold']:
            if detect_rsi_oversold(ticker, data, threshold=settings['rsi_oversold_threshold']):
                conditions_met.append('rsi_oversold')
        
        if preferences['rsi_overbought']:
            if detect_rsi_overbought(ticker, data, threshold=settings['rsi_overbought_threshold']):
                conditions_met.append('rsi_overbought')
        
        if preferences['sma_bull_trend']:
            if check_if_sma_short_window_is_above_long_window(ticker, short_window=settings['short_sma_bull_trend'], long_window=settings['long_sma_bull_trend'], data=data):
                conditions_met.append('sma_bull_trend')
        
        if preferences['sma_bear_trend']:
            if not check_if_sma_short_window_is_above_long_window(ticker, short_window=settings['short_sma_bear_trend'], long_window=settings['long_sma_bear_trend'], data=data):
                conditions_met.append('sma_bear_trend')
        
        if len(conditions_met) == sum(preferences.values()):
            notifications.append(f"All conditions met for {ticker}. Conditions: {conditions_met}")
    else:
        if preferences['golden_cross']:
            if detect_golden_cross_sma(ticker, data, short_window=settings['short_sma_golden'], long_window=settings['long_sma_golden']):
                notifications.append(f"Golden Cross detected for {ticker} in the last {settings['sma_golden_alert_window_days']} days. Long SMA: {settings['long_sma_golden']}, Short SMA: {settings['short_sma_golden']}")
        
        if preferences['death_cross']:
            if detect_death_cross_sma(ticker, data, short_window=settings['short_sma_death'], long_window=settings['long_sma_death']):
                notifications.append(f"Death Cross detected for {ticker} in the last {settings['sma_death_alert_window_days']} days. Long SMA: {settings['long_sma_death']}, Short SMA: {settings['short_sma_death']}")
        
        if preferences['rsi_oversold']:
            if detect_rsi_oversold(ticker, data, threshold=settings['rsi_oversold_threshold']):
                notifications.append(f"RSI Oversold condition detected for {ticker} today. Settings: {settings['rsi_oversold_threshold']}")
        
        if preferences['rsi_overbought']:
            if detect_rsi_overbought(ticker, data, threshold=settings['rsi_overbought_threshold']):
                notifications.append(f"RSI Overbought condition detected for {ticker} today. Settings: {settings['rsi_overbought_threshold']}")
        
        if preferences['sma_bull_trend']:
            if check_if_sma_short_window_is_above_long_window(ticker, short_window=settings['short_sma_bull_trend'], long_window=settings['long_sma_bull_trend'], data=data):
                notifications.append(f"BULLISH - SMA {settings['short_sma_bull_trend']} is above SMA {settings['long_sma_bull_trend']} for {ticker}")
        
        if preferences['sma_bear_trend']:
            if not check_if_sma_short_window_is_above_long_window(ticker, short_window=settings['short_sma_bear_trend'], long_window=settings['long_sma_bear_trend'], data=data):
                notifications.append(f"BEARISH - SMA {settings['short_sma_bear_trend']} is below SMA {settings['long_sma_bear_trend']} for {ticker}")

    return notifications


def detect_golden_cross_sma(ticker, data=None, short_window=50, long_window=200, alert_window_days=2):
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

    if golden_cross.iloc[-alert_window_days:].any():
        return True

    return False

def detect_death_cross_sma(ticker, data=None, short_window=50, long_window=200, alert_window_days=2):
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
    
    if death_cross.iloc[-alert_window_days:].any():
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