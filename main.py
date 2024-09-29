import streamlit as st
import pandas as pd
import utils.supabase as db
import utils.indicator_evaluator as ie

# import streamlit_analytics
import utils.telegram_controller as tc
import utils.ticker_getter as tg

import threading
from fastapi import FastAPI
import uvicorn


# # Create a FastAPI app instance
# app = FastAPI()

# # Create a separate thread to run FastAPI alongside Streamlit
# def run_fastapi():
#     uvicorn.run(app, host="0.0.0.0", port=8502)

# @app.post("/refresh-cache")
# async def refresh_cache():
#     print("REFRESHING CACHE")
#     settings = {
#         "tickers": dow_jones_tickers,
#         "indicator_settings": {
#             "apex_bull_appear": {"is_enabled": True},
#             "apex_bull_raging": {"is_enabled": True},
#             "apex_uptrend": {"is_enabled": True},
#         },
#         "show_win_rate": False,
#         "show_only_if_all_signals_met": True,
#         "show_only_market_price_above": 20,
#         "recency": 5,
#         "x": 20,
#     }

#     for count, ticker in enumerate(settings["tickers"], start=1):
#         result = ie.analyze_stock(ticker, settings)
#         print(count / len(settings["tickers"]))
    
#     return {"status": "Cache refreshed successfully!"}

# # Start FastAPI in a separate thread
# threading.Thread(target=run_fastapi, daemon=True).start()



dow_jones_tickers = tg.get_dow_jones()
sp500_tickers = tg.get_snp_500()
all_tickers = tg.get_all_tickers()

ticker_selection_options = all_tickers + ["ALL", "S&P 500", "Dow Jones"]
# get url parameters
show_params = st.query_params.get("show")



# Function to display ticker input with autocomplete and multi-select
def ticker_input(key="ticker_input", default=None):
    selected_tickers = st.multiselect(
        "Step 1: Select stock tickers",
        options=ticker_selection_options,
        key=key,
        default=default,
        placeholder="'ALL', 'S&P 500', 'Dow Jones' or add individual stock tickers",
    )
    return selected_tickers


# Updated indicators multiselect box and expander settings
def get_user_inputs(settings=None):
    if settings is None:
        settings = {
            "tickers": ["ALL"],
            "indicator_settings": {
                "golden_cross_sma": {
                    "is_enabled": False,
                    "short_sma": 50,
                    "long_sma": 200,
                },
                "death_cross_sma": {
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
            "show_win_rate": False,
            "show_only_if_all_signals_met": True,
            "show_only_market_price_above": 20,
            "recency": 5,
            "x": 20,
        }

    if show_params == "apex":
        # settings["indicator_settings"]["apex_bear_raging"] = {
        #     "is_enabled": True,
        # }
        settings["indicator_settings"]["apex_bull_raging"] = {
            "is_enabled": False,
        }
        settings["indicator_settings"]["apex_uptrend"] = {
            "is_enabled": False,
        }
        # settings["indicator_settings"]["apex_downtrend"] = {
        # "is_enabled": True,
        # }
        settings["indicator_settings"]["apex_bull_appear"] = {
            "is_enabled": False,
        }

    # Use the ticker_input function for adding tickers
    settings["tickers"] = ticker_input(default=settings.get("tickers", []))
    if "ALL" in settings["tickers"]:
        # TODO: remove all other tickers from the list if "ALL" is chosen
        settings["tickers"] = all_tickers  # Select all tickers if "ALL" is chosen
    if "S&P 500" in settings["tickers"]:
        settings["tickers"] = sp500_tickers
    if "Dow Jones" in settings["tickers"]:
        settings["tickers"] = dow_jones_tickers

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
        # if indicator == "apex_bear_raging":
        #     with st.expander("Apex Bear Raging Settings", expanded=False):
        #         st.caption(
        #             "Apex Bear Raging is a signal that occurs when there are majority bullish flush up bars, starting from more than 1/2 way since the latest bear trap, and reaches previous bull trap, rebounding back into the range"
        #         )
        # if indicator == "apex_bull_raging":
        #     with st.expander("Apex Bull Raging Settings", expanded=False):
        #         st.caption(
        #             "Apex Bull Raging is a signal that occurs when there are majority bearish flush down bars, starting from more than 1/2 way since the latest bull trap, and reaches previous bear trap, rebounding back into the range"
        #         )
        # if indicator == "apex_uptrend":
        #     with st.expander("Apex Uptrend Settings", expanded=False):
        #         st.caption(
        #             "Apex Uptrend is a signal that occurs when there is lightning or M formation, above sma 50 and 200."
        #         )
        # if indicator == "apex_downtrend":
        #     with st.expander("Apex Downtrend Settings", expanded=False):
        #         st.caption(
        #             "Apex Downtrend is a signal that occurs when there is N or W formation, below sma 50"
        #         )
        # if indicator == "apex_bull_appear":
        #     with st.expander("Apex Bull Appear Settings", expanded=False):
        #         st.caption(
        #             "Apex Bull Appear is a signal that occurs when there is a Kangaroo/ wallaby formation and a bullish bar (within up to 4 bars) after the wallaby, breaking from below Kangaroo Low, back into Kangaroo's price range."
        #         )
        # if indicator == "apex_bear_appear":
        #     with st.expander("Apex Bear Appear Settings", expanded=False):
        #         st.caption(
        #             "Apex Bear Appear is a signal that occurs when there is a Kangaroo/ wallaby formation and a bearish bar (within up to 4 bars) after the wallaby, breaking from above Kangaroo High back into Kangaroo's price range."
        #         )
        if indicator == "golden_cross_sma":
            with st.expander("Golden Cross Settings", expanded=False):
                st.caption(
                    "Golden Cross is a bullish signal that occurs when the short-term moving average crosses above the long-term moving average."
                )
                settings["indicator_settings"]["golden_cross_sma"]["short_sma"] = (
                    st.number_input(
                        "Short SMA window for Golden Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["golden_cross_sma"][
                            "short_sma"
                        ],
                    )
                )
                settings["indicator_settings"]["golden_cross_sma"]["long_sma"] = (
                    st.number_input(
                        "Long SMA window for Golden Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["golden_cross_sma"][
                            "long_sma"
                        ],
                    )
                )

        if indicator == "death_cross_sma":
            with st.expander("Death Cross Settings", expanded=False):
                st.caption(
                    "Death Cross is a bearish signal that occurs when the short-term moving average crosses below the long-term moving average."
                )
                settings["indicator_settings"]["death_cross_sma"]["short_sma"] = (
                    st.number_input(
                        "Short SMA window for Death Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["death_cross_sma"][
                            "short_sma"
                        ],
                    )
                )
                settings["indicator_settings"]["death_cross_sma"]["long_sma"] = (
                    st.number_input(
                        "Long SMA window for Death Cross:",
                        min_value=1,
                        value=settings["indicator_settings"]["death_cross_sma"][
                            "long_sma"
                        ],
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

    # recency of data to look at (int)
    settings["recency"] = st.number_input(
        "Step 3: Select recency of signal (# trading days) to include in results ",
        min_value=1,
        value=settings.get("recency", 5),
    )

    with st.expander("Advanced Settings", expanded=False):
        st.caption("Advanced settings for calculating success rate and % change")

        settings["show_win_rate"] = st.checkbox(
            "Show historical win rate (would result in roughly 10x slower analysis)",
            value=settings.get("show_win_rate", False),
        )

        # create input for user to select number of days to look forward to calculate success rate and % change
        if settings["show_win_rate"]:
            settings["x"] = st.number_input(
                "Select number of trading days to look forward for success rate and % change calculation",
                min_value=1,
                value=settings.get("x", 7),
            )

        filter_market_price = st.checkbox(
            "Filter by market price",
            value=settings.get("show_only_market_price_above", 0) != 0,
        )
        if filter_market_price:
            settings["show_only_market_price_above"] = st.number_input(
                "Only screen stocks where current market price is above",
                min_value=0,
                value=settings.get("show_only_market_price_above", 0),
            )

        settings["show_only_if_all_signals_met"] = st.checkbox(
            "Show only if all signals are met",
            value=settings.get("show_only_if_all_signals_met", True),
        )

    return settings


# with streamlit_analytics.track(unsafe_password="test123"):
st.title("Optilens Stock Screener 📈")
st.subheader("Find stocks using technical indicators")

st.sidebar.subheader("Any feedback/ feature requests?")

feedback = st.sidebar.text_area("", height=100)
submit_feedback = st.sidebar.button("Submit")
if submit_feedback:
    tc.send_message(message="User feedback received: \n" + feedback)
    st.sidebar.success(
        f"Feedback '{feedback}' submitted successfully. Thank you for your feedback!"
    )


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

        # Placeholder for overall probability calc
        overall_success_rate_placeholder = st.empty()
        overall_change_percent_placeholder = st.empty()
        overall_num_instances_placeholder = st.empty()

        overall_num_instances = 0
        overall_num_instances_rise = 0
        overall_change_percent = 0

        # Placeholder for the DataFrame that will be updated
        dataframe_placeholder = st.empty()

        for count, ticker in enumerate(settings["tickers"], start=1):
            result = ie.analyze_stock(ticker, settings)
            progress_bar.progress(count / total_tickers)
            progress_text_placeholder.info(f"Screening {count}/{total_tickers} tickers")

            if result is not None:
                if settings["show_win_rate"]:
                    overall_num_instances += result["total_instances"]
                    overall_num_instances_rise += (
                        result["total_instances"] * result["success_rate"] / 100
                    )
                    overall_change_percent += (
                        result["total_instances"] * result["avg_percentage_change"]
                    )

                    if (
                        result["common_dates"] is not None
                        and len(result["common_dates"]) > 0
                    ):
                        # Create a new DataFrame for the new row
                        new_row = pd.DataFrame(
                            {
                                "Ticker": [ticker],
                                "Signal entry dates": [result["common_dates"]],
                                "# Occurances": result["total_instances"],
                                f"% Chance stock rises {settings["x"]} days later": result[
                                    "success_rate"
                                ],
                                f"Avg change % {settings["x"]} days later": result[
                                    "avg_percentage_change"
                                ],
                            }
                        )

                        # Concatenate the new row with the existing DataFrame
                        screening_results = pd.concat(
                            [screening_results, new_row], ignore_index=True
                        )

                        # Update overall stats in frontend
                        overall_success_rate_placeholder.metric(
                            "Overall Chance Rises X days later(%)",
                            round(
                                overall_num_instances_rise
                                / overall_num_instances
                                * 100,
                                2,
                            ),
                        )
                        overall_change_percent_placeholder.metric(
                            "Overall Change percent X days later(%)",
                            round(overall_change_percent / overall_num_instances, 2),
                        )
                        overall_num_instances_placeholder.metric(
                            "Overall Number of instances", overall_num_instances
                        )
                        # Update the DataFrame in the frontend
                        dataframe_placeholder.dataframe(
                            screening_results, width=1000, hide_index=True
                        )
                else:
                    if (
                        result["common_dates"] is not None
                        and len(result["common_dates"]) > 0
                    ):
                        # Create a new DataFrame for the new row
                        new_row = pd.DataFrame(
                            {
                                "Ticker": [ticker],
                                "Signal entry dates": [result["common_dates"]],
                            }
                        )

                        # Concatenate the new row with the existing DataFrame
                        screening_results = pd.concat(
                            [screening_results, new_row], ignore_index=True
                        )

                        # Update the DataFrame in the frontend
                        dataframe_placeholder.dataframe(
                            screening_results, width=1000, hide_index=True
                        )

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
