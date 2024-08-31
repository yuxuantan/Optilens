import streamlit as st
from typing import List, Dict, Any, Optional
import pandas as pd
import controllers.telegram_controller as tc
import controllers.indicator_evaluator as ie
import controllers.supabase_controller as db

# Type aliases for clarity
Ticker = str
AlertName = str
AlertSettings = Dict[str, Any]


def get_user_inputs(
    user_data: Dict, default_settings: Optional[AlertSettings] = None
) -> AlertSettings:
    """Get user inputs for alert settings."""
    if default_settings is None:
        default_settings = {
            "tickers": [],
            "preferences": {
                "golden_cross": False,
                "death_cross": False,
                "rsi_overbought": False,
                "rsi_oversold": False,
                "sma_bull_trend": False,
                "sma_bear_trend": False,
            },
            "short_sma_golden": 50,
            "long_sma_golden": 200,
            "sma_golden_alert_window_days": 2,
            "short_sma_death": 50,
            "long_sma_death": 200,
            "sma_death_alert_window_days": 2,
            "rsi_overbought_threshold": 70,
            "rsi_oversold_threshold": 30,
            "short_sma_bull_trend": 50,
            "long_sma_bull_trend": 200,
            "short_sma_bear_trend": 50,
            "long_sma_bear_trend": 200,
            "include_only_if_all_conditions_satisfied": True,
            "alert_method": "Telegram",
            "alert_interval": 1,
            "alert_enabled": False,
        }

    tickers = st.text_area(
        "Enter stock ticker symbols (comma-separated):",
        value=", ".join(default_settings["tickers"]),
    )
    if tickers == "ALL":
        tickers = pd.read_csv("./sp500_companies.csv")["Symbol"].tolist()
    else:
        tickers = [ticker.strip() for ticker in tickers.split(",") if ticker.strip()]

    preferences = {}
    settings = {}
    st.subheader("Filter Preferences")
    st.caption("Select the indicators you want to filter for.")
    

    
    col1, col2 = st.columns(2)
    with col1:
        st.write("Bullish")
        preferences["golden_cross"] = st.checkbox(
            "Golden Cross (BULL)",
            value=default_settings["preferences"]["golden_cross"],
        )

        with st.expander("Golden Cross Settings", expanded=False):
            settings["short_sma_golden"] = st.number_input(
                "Short SMA window for Golden Cross:",
                min_value=1,
                value=default_settings["short_sma_golden"],
            )
            settings["long_sma_golden"] = st.number_input(
                "Long SMA window for Golden Cross:",
                min_value=1,
                value=default_settings["long_sma_golden"],
            )
            settings["sma_golden_alert_window_days"] = st.number_input(
                "Alert window for Golden Cross (in days):",
                min_value=1,
                value=default_settings["sma_golden_alert_window_days"],
            )

        preferences["rsi_oversold"] = st.checkbox(
            "RSI Oversold (BULL)",
            value=default_settings["preferences"]["rsi_oversold"],
        )

        with st.expander("RSI Oversold Settings", expanded=False):
            settings["rsi_oversold_threshold"] = st.number_input(
                "RSI oversold threshold:",
                min_value=0,
                max_value=100,
                value=default_settings["rsi_oversold_threshold"],
            )

        preferences["sma_bull_trend"] = st.checkbox(
            "SMA bull trend (Short SMA above Long SMA)",
            value=default_settings["preferences"]["sma_bull_trend"],
        )

        with st.expander("SMA bull trend Settings", expanded=False):
            settings["short_sma_bull_trend"] = st.number_input(
                "Short SMA window for Bull Trend:",
                min_value=1,
                value=default_settings["short_sma_bull_trend"],
            )
            settings["long_sma_bull_trend"] = st.number_input(
                "Long SMA window for Bull Trend:",
                min_value=1,
                value=default_settings["long_sma_bull_trend"],
            )

    with col2:
        st.write("Bearish")
        preferences["death_cross"] = st.checkbox(
            "Death Cross (BEAR)",
            value=default_settings["preferences"]["death_cross"],
        )

        with st.expander("Death Cross Settings", expanded=False):
            settings["short_sma_death"] = st.number_input(
                "Short SMA window for Death Cross:",
                min_value=1,
                value=default_settings["short_sma_death"],
            )
            settings["long_sma_death"] = st.number_input(
                "Long SMA window for Death Cross:",
                min_value=1,
                value=default_settings["long_sma_death"],
            )
            settings["sma_death_alert_window_days"] = st.number_input(
                "Alert window for Death Cross (in days):",
                min_value=1,
                value=default_settings["sma_death_alert_window_days"],
            )

        preferences["rsi_overbought"] = st.checkbox(
            "RSI Overbought (BEAR)",
            value=default_settings["preferences"]["rsi_overbought"],
        )

        with st.expander("RSI Overbought Settings", expanded=False):
            settings["rsi_overbought_threshold"] = st.number_input(
                "RSI overbought threshold:",
                min_value=0,
                max_value=100,
                value=default_settings["rsi_overbought_threshold"],
            )
                
        preferences["sma_bear_trend"] = st.checkbox(
            "SMA bear trend (Short SMA below Long SMA)",
            value=default_settings["preferences"]["sma_bear_trend"],
        )

        with st.expander("SMA bear trend Settings", expanded=False):
            settings["short_sma_bear_trend"] = st.number_input(
                "Short SMA window for Bear Trend:",
                min_value=1,
                value=default_settings["short_sma_bear_trend"],
            )
            settings["long_sma_bear_trend"] = st.number_input(
                "Long SMA window for Bear Trend:",
                min_value=1,
                value=default_settings["long_sma_bear_trend"],
            )
                
    st.subheader("Filter inclusion criteria")
    # checkbox to specify whether conditions should be AND or OR
    settings['include_only_if_all_conditions_satisfied'] = st.checkbox("All above conditions must be met", value=True)
    
    st.subheader("Alert Settings")
    alert_enabled = st.toggle("Enable alert", value=default_settings["alert_enabled"])
    alert_method = default_settings["alert_method"]
    alert_interval = default_settings["alert_interval"]
    if alert_enabled:
        alert_method = st.selectbox(
            "Select alert method:",
            ["Telegram", "Email", "SMS"],
            index=["Telegram", "Email", "SMS"].index(default_settings["alert_method"]),
        )
        if alert_method == "Telegram":
            if user_data.get("user", {}).get("telegram_chat_id"):
                st.success("✅ Telegram bot is already set up")
            else:
                st.warning(
                    "⚠️ You do not have a Telegram bot set up. Dm https://t.me/yxfinance_bot and enter your user_id to set up the bot."
                )
        alert_interval = st.number_input(
            "Alert interval (in minutes):",
            min_value=1,
            value=default_settings["alert_interval"],
        )

       

    return {
        "tickers": tickers,
        "preferences": preferences,
        **settings,
        "alert_method": alert_method,
        "alert_interval": alert_interval,
        "alert_enabled": alert_enabled,
    }


def stock_screener_page(user_data):
    user_id = user_data["user"]["user_id"]

    saved_alerts = user_data.get("alerts", {}) or {}
    print(saved_alerts)
    saved_alerts = {alert["alert_name"]: alert["settings"] for alert in saved_alerts}

    if "alerts" not in st.session_state:
        st.session_state.alerts = saved_alerts

    st.title("Stock Analyzer")

    alert_names = list(st.session_state.alerts.keys())
    alert_names.insert(0, "Create New Alert")
    selected_alert = st.sidebar.selectbox(
        "Select an alert or create a new one:", options=alert_names
    )

    if selected_alert == "Create New Alert":
        alert_name = st.text_input("Name your alert configuration:")
        settings = get_user_inputs(user_data)
        save_button = st.button("Save Alert")
    else:
        alert_name = selected_alert
        settings = get_user_inputs(user_data, st.session_state.alerts[selected_alert])
        col1, col2, col3 = st.columns(3)
        save_button = col1.button("Update Alert")
        delete_button = col2.button("Delete Alert")
        analyze_button = col3.button("Run Analysis")

    if save_button:
        if alert_name and settings["tickers"]:
            if selected_alert == "Create New Alert":
                db.create_user_alert(user_id, alert_name, settings)
            else:
                db.update_user_alert(user_id, alert_name, settings)
            st.success(f"Alert '{alert_name}' saved successfully!")
            if settings.get("alert_method") == "Telegram":
                tc.send_message(
                    user_data["user"].get("telegram_chat_id"),
                    f"Alert '{alert_name}' saved successfully!",
                )
            st.rerun()
        else:
            st.error("Please enter an alert name and at least one stock ticker symbol.")

    if selected_alert != "Create New Alert" and delete_button:
        db.delete_user_alert(user_id, selected_alert)
        del st.session_state.alerts[selected_alert]
        st.success(f"Alert '{selected_alert}' deleted successfully!")
        st.rerun()

    if selected_alert != "Create New Alert" and analyze_button:
        if settings["tickers"]:
            progress_bar = st.progress(0)
            total_tickers = len(settings["tickers"])
            result_text = f"*Ran analysis for alert '{alert_name}'*\n"
            analysis_results = []
            for count, ticker in enumerate(settings["tickers"], start=1):
                notifications = ie.analyze_stock(
                    ticker, settings
                )
                progress_bar.progress(count / total_tickers)
                if len(notifications) > 0:
                    # analysis_results += f"\n### Analysis for {ticker}\n"
                    # st.markdown(f"### Analysis for {ticker}")
                    for notification in notifications:
                        analysis_results.append(notification)
                        st.warning(notification)
            progress_bar.empty()
            if len(analysis_results)==0:
                analysis_results.append("No alerts found for the selected stocks.")
            tc.send_message(user_data["user"].get("telegram_chat_id"), result_text)
            for result in analysis_results:
                tc.send_message(user_data["user"].get("telegram_chat_id"), f"- {result}")
