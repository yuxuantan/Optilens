import yfinance as yf
import pandas as pd

# Define the stock ticker symbol
ticker_symbol = "AAPL"

# Fetch the stock data
stock = yf.Ticker(ticker_symbol)

# Get the earnings dates DataFrame
earnings_dates_df = stock.earnings_dates

# Convert the current timestamp to match the DataFrame's timezone
current_time = pd.Timestamp.now(tz=earnings_dates_df.index.tz)

# Filter and get the next upcoming earnings date
next_earnings_date = earnings_dates_df[earnings_dates_df.index > current_time].index.min()

# Display the next earnings date
print(f"The next earnings date for {ticker_symbol} is: {next_earnings_date}")
