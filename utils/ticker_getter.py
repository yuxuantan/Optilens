import streamlit as st
import pandas as pd
import yfinance as yf

from pytickersymbols import PyTickerSymbols
from get_all_tickers import get_tickers as gt

# @st.cache_data(ttl="1d")
def fetch_stock_data(ticker, period='max', interval='1d') -> pd.DataFrame:
    try:
        data = yf.download(ticker, period=period, interval=interval)
        return data
    except Exception as e:
        print(f"Failed to fetch data for {ticker}")
        return None
    
# @st.cache_data(ttl="1d")
def get_all_tickers():
    tickers = gt.get_tickers()
    print(tickers[:5])
    return tickers
    
# @st.cache_data(ttl="1d")
def get_snp_500():
    stock_data = PyTickerSymbols()
    sp500_tickers = [stock['symbol'] for stock in stock_data.get_stocks_by_index('S&P 500')]
    return sp500_tickers

# @st.cache_data(ttl="1d")
def get_dow_jones():
    stock_data = PyTickerSymbols()
    dow_jones_tickers = [stock['symbol'] for stock in stock_data.get_stocks_by_index('Dow Jones')]
    return dow_jones_tickers


