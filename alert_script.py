import utils.indicator_evaluator as ie
import utils.telegram_controller as tc
import utils.ticker_getter as tg

chat_ids = [
    27392018,  # me
    432502167 # rainbow
]

shared_settings = {
    "show_win_rate": False,
    "show_only_if_all_signals_met": True,
    "show_only_market_price_above": 20,
    "recency": 5,
    "x": 20,
    "indicator_settings": {
        "apex_bull_appear": {
            "is_enabled": False
        },
        "apex_bull_raging": {
            "is_enabled": False
        },
    }
}

stock_list = tg.get_all_tickers()
# stock_list = tg.get_snp_500()
# stock_list = tg.get_dow_jones()
screening_pool_msg = "⚙️ Screening pool: All stocks with market px above 20"
chart_interval_msg = "⚙️ Chart Interval: 2D"


def alert_bull_raging():
    settings = shared_settings.copy()
    settings["indicator_settings"]["apex_bull_raging"]["is_enabled"] = True

    overall_num_instances = 0
    overall_num_instances_rise = 0
    overall_change_percent = 0

    output_msg = ""

    for ticker in stock_list:
        print(f"Analyzing {ticker}")
        result = ie.analyze_stock(ticker, settings)

        if result is not None:
            if settings["show_win_rate"]:
                overall_num_instances += result["total_instances"]
                overall_num_instances_rise += (
                    result["total_instances"] * result["success_rate"] / 100
                )
                overall_change_percent += (
                    result["total_instances"] * result["avg_percentage_change"]
                )

            if result["common_dates"] is not None:
                output_msg = (
                    f"{output_msg}\n✅ *{ticker}* - {result['common_dates'][-1]}"
                )
                # Create a new DataFrame for the new row

    if output_msg == "":
        output_msg = "No stocks found matching the criteria"

    output_msg = f"""*Bull raging screening completed*
⚙️ Recency: {settings['recency']} days
{screening_pool_msg}
{chart_interval_msg}

Screen results (Ticker - Last Bull Raging Entry Date):
{output_msg}
"""
    # Avg win rate (stock rise) 1mth later(%): {round(overall_num_instances_rise/overall_num_instances*100, 2)}
    # Avg price change 1mth later(%): {round(overall_change_percent/overall_num_instances, 2)}
    return output_msg


def alert_bull_appear():
    settings = shared_settings.copy()
    settings["indicator_settings"]["apex_bull_appear"]["is_enabled"] = True
    

    overall_num_instances = 0
    overall_num_instances_rise = 0
    overall_change_percent = 0

    output_msg = ""

    for ticker in stock_list:
        print(f"Analyzing {ticker}")
        result = ie.analyze_stock(ticker, settings)
        if result is not None:
            if settings["show_win_rate"]:
                overall_num_instances += result["total_instances"]
                overall_num_instances_rise += (
                    result["total_instances"] * result["success_rate"] / 100
                )
                overall_change_percent += (
                    result["total_instances"] * result["avg_percentage_change"]
                )

            if result["common_dates"] is not None:
                output_msg = (
                    f"{output_msg}\n✅ *{ticker}* - {result['common_dates'][-1]}"
                )
                # Create a new DataFrame for the new row

    if output_msg == "":
        output_msg = "No stocks found matching the criteria"

    output_msg = f""" *Bull appear screening completed*
⚙️ Recency: {settings['recency']} days
{screening_pool_msg}
{chart_interval_msg}

Screen results (Ticker - Last Bull Appear Entry Date):
{output_msg}
"""
    return output_msg


if __name__ == "__main__":
    for chat in chat_ids:
        tc.send_message(chat_id=chat, message="Starting screening for bull appear..")

    bull_appear_msg = alert_bull_appear()

    for chat in chat_ids:
        tc.send_message(chat_id=chat, message=bull_appear_msg)
        tc.send_message(chat_id=chat, message="Starting screening for bull raging..")

    bull_raging_msg = alert_bull_raging()
    for chat in chat_ids:
        tc.send_message(chat_id=chat, message=bull_raging_msg)
