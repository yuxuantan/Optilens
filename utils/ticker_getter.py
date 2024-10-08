import streamlit as st
import pandas as pd
import yfinance as yf

from pytickersymbols import PyTickerSymbols
import requests
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
# import requests

def fetch_next_earnings_date(ticker_symbol):
        
    # Fetch the stock data
    stock = yf.Ticker(ticker_symbol)

    # Get the earnings dates DataFrame
    earnings_dates_df = stock.earnings_dates

    # Ensure the current time has the same timezone as the earnings dates DataFrame

    # Get the next upcoming earnings date by filtering dates greater than current time
    if earnings_dates_df is not None and not earnings_dates_df.empty:
        current_time = pd.Timestamp.now().tz_localize(earnings_dates_df.index.tz)
        next_earnings_date = earnings_dates_df[earnings_dates_df.index > current_time].index.min()
        return next_earnings_date
    else:
        print(f"No earnings dates found for {ticker_symbol}")
        return None


def get_all_tickers():
    # fetch from file sec_company_tickers.json
    url = "sec_company_tickers.json"
    data = pd.read_json(url)
    # switch row and column
    data = data.T
    # get ticker symbols
    tickers = data['ticker'].tolist()

    # tickers = gt.get_tickers()
    # print(tickers[:5])
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


