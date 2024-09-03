import streamlit as st
import pandas as pd
import utils.supabase as db
import utils.indicator_evaluator as ie
import streamlit_analytics
import utils.telegram_controller as tc

# Load S&P 500 tickers
sp500_df = pd.read_csv("./sp500_companies.csv")
sp500_tickers = sp500_df["Symbol"].tolist()

all_df = pd.read_csv("./Stocks_data.csv")
all_tickers = all_df["symbol"].tolist()

ticker_selection_options = all_tickers + ["ALL", "S&P 500"]

# Function to display ticker input with autocomplete and multi-select
def ticker_input(key="ticker_input", default=None):
    selected_tickers = st.multiselect(
        "Step 1: Select stock tickers",
        options=ticker_selection_options,
        key=key,
        default=default,
        placeholder="Select 'ALL' to include all tickers. Select 'S&P 500' to include all S&P 500 tickers.",
    )
    return selected_tickers


# Updated indicators multiselect box and expander settings
def get_user_inputs(settings=None):
    if settings is None:
        settings = {
            "tickers": [],
            "indicator_settings": {
                "golden_cross": {
                    "is_enabled": False,
                    "short_sma": 50,
                    "long_sma": 200,
                },
                "death_cross": {
                    "is_enabled": False,
                    "short_sma": 50,
                    "long_sma": 200,
                },
                "rsi_overbought": {
                    "is_enabled": False,
                    "threshold": 70,
                },
                "rsi_oversold": {
                    "is_enabled": False,
                    "threshold": 30,
                },
                "macd_bullish": {
                    "is_enabled": False,
                    "short_ema": 12,
                    "long_ema": 26,
                    "signal_window": 9,
                },
                "macd_bearish": {
                    "is_enabled": False,
                    "short_ema": 12,
                    "long_ema": 26,
                    "signal_window": 9,
                },
                "bollinger_squeeze": {
                    "is_enabled": False,
                    "window": 20,
                    "num_std_dev": 2,
                },
                "bollinger_expansion": {
                    "is_enabled": False,
                    "window": 20,
                    "num_std_dev": 2,
                },
                "bollinger_breakout": {
                    "is_enabled": False,
                    "window": 20,
                    "num_std_dev": 2,
                },
                "bollinger_pullback": {
                    "is_enabled": False,
                    "window": 20,
                    "num_std_dev": 2,
                },
                "volume_spike": {
                    "is_enabled": False,
                    "window": 20,
                    "num_std_dev": 2,
                },
            },
            "x": 7
        }

    # Use the ticker_input function for adding tickers
    settings["tickers"] = ticker_input(default=settings.get("tickers", []))
    if "ALL" in settings["tickers"]:
        # TODO: remove all other tickers from the list if "ALL" is chosen
        settings["tickers"] = all_tickers  # Select all tickers if "ALL" is chosen
    if "S&P 500" in settings["tickers"]:
        settings["tickers"] = sp500_tickers

    # Dropdown for selecting indicators
    selected_indicators = st.multiselect(
        "Step 2: Select technical indicators",
        options=list(settings["indicator_settings"].keys()),
        default=[
            k for k, v in settings["indicator_settings"].items() if v["is_enabled"]
        ],
    )

    for indicator in selected_indicators:
        settings["indicator_settings"][indicator]["is_enabled"] = True

        if indicator == "golden_cross":
            with st.expander("Golden Cross Settings", expanded=False):
                st.caption(
                    "Golden Cross is a bullish signal that occurs when the short-term moving average crosses above the long-term moving average."
                )
                settings["indicator_settings"]["golden_cross"]["short_sma"] = (
                    st.number_input(
                        "Short SMA window for Golden Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["golden_cross"][
                            "short_sma"
                        ],
                    )
                )
                settings["indicator_settings"]["golden_cross"]["long_sma"] = (
                    st.number_input(
                        "Long SMA window for Golden Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["golden_cross"][
                            "long_sma"
                        ],
                    )
                )

        if indicator == "death_cross":
            with st.expander("Death Cross Settings", expanded=False):
                st.caption(
                    "Death Cross is a bearish signal that occurs when the short-term moving average crosses below the long-term moving average."
                )
                settings["indicator_settings"]["death_cross"]["short_sma"] = (
                    st.number_input(
                        "Short SMA window for Death Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["death_cross"][
                            "short_sma"
                        ],
                    )
                )
                settings["indicator_settings"]["death_cross"]["long_sma"] = (
                    st.number_input(
                        "Long SMA window for Death Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["death_cross"]["long_sma"],
                    )
                )

        if indicator == "rsi_overbought":
            with st.expander("RSI Overbought Settings", expanded=False):
                st.caption(
                    "RSI Overbought is a bearish signal that occurs when the Relative Strength Index (RSI) is above a certain threshold."
                )
                settings["indicator_settings"]["rsi_overbought"]["threshold"] = (
                    st.number_input(
                        "RSI Overbought threshold:",
                        min_value=1,
                        max_value=100,
                        value=settings["indicator_settings"]["rsi_overbought"][
                            "threshold"
                        ],
                    )
                )

        if indicator == "rsi_oversold":
            with st.expander("RSI Oversold Settings", expanded=False):
                st.caption(
                    "RSI Oversold is a bullish signal that occurs when the Relative Strength Index (RSI) is below a certain threshold."
                )
                settings["indicator_settings"]["rsi_oversold"]["threshold"] = (
                    st.number_input(
                        "RSI Oversold threshold:",
                        min_value=1,
                        max_value=100,
                        value=settings["indicator_settings"]["rsi_oversold"][
                            "threshold"
                        ],
                    )
                )

        if indicator == "macd_bullish":
            with st.expander("MACD Bullish Settings", expanded=False):
                st.caption(
                    "MACD Bullish is a bullish signal that occurs when the MACD line crosses above the signal line."
                )
                settings["indicator_settings"]["macd_bullish"]["short_ema"] = (
                    st.number_input(
                        "Short EMA for MACD Bullish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bullish"][
                            "short_ema"
                        ],
                    )
                )
                settings["indicator_settings"]["macd_bullish"]["long_ema"] = (
                    st.number_input(
                        "Long EMA for MACD Bullish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bullish"][
                            "long_ema"
                        ],
                    )
                )
                settings["indicator_settings"]["macd_bullish"]["signal_window"] = (
                    st.number_input(
                        "Signal line window for MACD Bullish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bullish"][
                            "signal_window"
                        ],
                    )
                )

        if indicator == "macd_bearish":
            with st.expander("MACD Bearish Settings", expanded=False):
                st.caption(
                    "MACD Bearish is a bearish signal that occurs when the MACD line crosses below the signal line."
                )
                settings["indicator_settings"]["macd_bearish"]["short_ema"] = (
                    st.number_input(
                        "Short EMA for MACD Bearish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bearish"][
                            "short_ema"
                        ],
                    )
                )
                settings["indicator_settings"]["macd_bearish"]["long_ema"] = (
                    st.number_input(
                        "Long EMA for MACD Bearish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bearish"][
                            "long_ema"
                        ],
                    )
                )
                settings["indicator_settings"]["macd_bearish"]["signal_window"] = (
                    st.number_input(
                        "Signal line window for MACD Bearish:",
                        min_value=1,
                        value=settings["indicator_settings"]["macd_bearish"][
                            "signal_window"
                        ],
                    )
                )

        if indicator == "bollinger_squeeze":
            with st.expander("Bollinger Squeeze Settings", expanded=False):
                st.caption(
                    "Bollinger Squeeze is a signal that occurs when the Bollinger Bands narrow, indicating lower volatility."
                )
                settings["indicator_settings"]["bollinger_squeeze"]["window"] = (
                    st.number_input(
                        "Bollinger Squeeze window:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_squeeze"][
                            "window"
                        ],
                    )
                )
                settings["indicator_settings"]["bollinger_squeeze"]["num_std_dev"] = (
                    st.number_input(
                        "Number of standard deviations for Bollinger Squeeze:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_squeeze"][
                            "num_std_dev"
                        ],
                    )
                )

        if indicator == "bollinger_expansion":
            with st.expander("Bollinger Expansion Settings", expanded=False):
                st.caption(
                    "Bollinger Expansion is a signal that occurs when the Bollinger Bands widen, indicating higher volatility."
                )
                settings["indicator_settings"]["bollinger_expansion"]["window"] = (
                    st.number_input(
                        "Bollinger Expansion window:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_expansion"][
                            "window"
                        ],
                    )
                )
                settings["indicator_settings"]["bollinger_expansion"]["num_std_dev"] = (
                    st.number_input(
                        "Number of standard deviations for Bollinger Expansion:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_expansion"][
                            "num_std_dev"
                        ],
                    )
                )

        if indicator == "bollinger_breakout":
            with st.expander("Bollinger Breakout Settings", expanded=False):
                st.caption(
                    "Bollinger Breakout is a signal that occurs when the price breaks out above the upper Bollinger Band."
                )
                settings["indicator_settings"]["bollinger_breakout"]["window"] = (
                    st.number_input(
                        "Bollinger Breakout window:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_breakout"][
                            "window"
                        ],
                    )
                )
                settings["indicator_settings"]["bollinger_breakout"]["num_std_dev"] = (
                    st.number_input(
                        "Number of standard deviations for Bollinger Breakout:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_breakout"][
                            "num_std_dev"
                        ],
                    )
                )

        if indicator == "bollinger_pullback":
            with st.expander("Bollinger Pullback Settings", expanded=False):
                st.caption(
                    "Bollinger Pullback is a signal that occurs when the price pulls back to the middle Bollinger Band after a breakout."
                )
                settings["indicator_settings"]["bollinger_pullback"]["window"] = (
                    st.number_input(
                        "Bollinger Pullback window:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_pullback"][
                            "window"
                        ],
                    )
                )
                settings["indicator_settings"]["bollinger_pullback"]["num_std_dev"] = (
                    st.number_input(
                        "Number of standard deviations for Bollinger Pullback:",
                        min_value=1,
                        value=settings["indicator_settings"]["bollinger_pullback"][
                            "num_std_dev"
                        ],
                    )
                )

        if indicator == "volume_spike":
            with st.expander("Volume Spike Settings", expanded=False):
                st.caption(
                    "Volume Spike is a signal that occurs when trading volume spikes significantly above average."
                )
                settings["indicator_settings"]["volume_spike"]["window"] = (
                    st.number_input(
                        "Volume Spike window:",
                        min_value=1,
                        value=settings["indicator_settings"]["volume_spike"]["window"],
                    )
                )
                settings["indicator_settings"]["volume_spike"]["num_std_dev"] = (
                    st.number_input(
                        "Number of standard deviations for Volume Spike:",
                        min_value=1,
                        value=settings["indicator_settings"]["volume_spike"][
                            "num_std_dev"
                        ],
                    )
                )
    
    # create input for user to select number of days to look forward to calculate success rate and % change
    settings["x"] = st.number_input(
        "Step 3: Select number of days to look forward for success rate and % change calculation",
        min_value=1,
        value=settings.get("x", 7),
    )
    return settings


with streamlit_analytics.track(unsafe_password="test123"):
    st.title("Optilens Stock Screener 📈")
    st.subheader("Find stocks using technical indicators")

    st.sidebar.subheader("What other features would you like to see on the app?")

    feedback = st.sidebar.text_area("", height=100)
    submit_feedback = st.sidebar.button("Submit")
    if submit_feedback:
        tc.send_message(message="User feedback received: \n" + feedback)
        st.sidebar.success(f"Feedback '{feedback}' submitted successfully. Thank you for your feedback!")
    


    # Get user inputs
    settings = get_user_inputs()
    screen_button_placeholder = st.empty()
    screen_button = screen_button_placeholder.button("🔎 Screen")


    if screen_button:
        if settings["tickers"]:
            # check if there is any indicators enabled in settings['indicator_settings']
            if (
                len(
                    [
                        k
                        for k, v in settings["indicator_settings"].items()
                        if v["is_enabled"]
                    ]
                )
                == 0
            ):
                st.error("Please enable at least one technical indicator.")
                st.stop()

            screen_button_placeholder.empty()
            stop_screening = screen_button_placeholder.button(
                "Stop screening", key="stop_screening"
            )
            if stop_screening:
                st.rerun()

            st.divider()
            st.header("Screening Results")
            progress_bar = st.progress(0)
            total_tickers = len(settings["tickers"])

            progress_text_placeholder = st.empty()
            screening_results = pd.DataFrame(columns=["Ticker"])

            # Placeholder for the DataFrame that will be updated
            dataframe_placeholder = st.empty()

            for count, ticker in enumerate(settings["tickers"], start=1):
                result = ie.analyze_stock(ticker, settings)
                progress_bar.progress(count / total_tickers)
                progress_text_placeholder.info(
                    f"Screening {count}/{total_tickers} tickers"
                )

                if result is not None:
                    # Create a new DataFrame for the new row
                    new_row = pd.DataFrame(
                        {
                            "Ticker": [ticker],
                            "Dates which fit conditions": [result["common_dates"]],
                            "Total instances": result["total_instances"],
                            f"% Chance stock rises {settings["x"]} days later": result["success_rate"],
                            f"Avg change % {settings["x"]} days later": result["avg_percentage_change"],
                        }
                    )

                    # Concatenate the new row with the existing DataFrame
                    screening_results = pd.concat(
                        [screening_results, new_row], ignore_index=True
                    )

                    # Update the DataFrame in the frontend
                    dataframe_placeholder.dataframe(screening_results, width=1000)

            progress_text_placeholder.success(
                f"Completed screening of {count}/{total_tickers} tickers"
            )
            progress_bar.empty()

            # recreate screen button after complete
            screen_button_placeholder.empty()
            screen_button_placeholder.button("🔎 Screen", key="screen_button")

            if screening_results.empty:
                st.warning(
                    "No signals detected for the selected tickers based on your screening criteria."
                )
        else:
            st.error("Please select at least one stock ticker symbol.")
