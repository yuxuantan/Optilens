import streamlit as st
import pandas as pd

from pytickersymbols import PyTickerSymbols
from get_all_tickers import get_tickers as gt

@st.cache_data(ttl="1d")
def get_all_tickers():
    tickers = gt.get_tickers()
    print(tickers[:5])
    return tickers
    
@st.cache_data(ttl="1d")
def get_snp_500():
    stock_data = PyTickerSymbols()
    sp500_tickers = [stock['symbol'] for stock in stock_data.get_stocks_by_index('S&P 500')]
    return sp500_tickers

@st.cache_data(ttl="1d")
def get_dow_jones():
    stock_data = PyTickerSymbols()
    dow_jones_tickers = [stock['symbol'] for stock in stock_data.get_stocks_by_index('Dow Jones')]
    return dow_jones_tickers


