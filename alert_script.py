import utils.indicator_evaluator as ie
import utils.telegram_controller as tc
import utils.ticker_getter as tg
import datetime

# stock_list = tg.get_all_tickers()
stock_list = tg.get_snp_500()
screening_pool_msg = "⚙️ Screening pool: All s&p 500 stocks with market px above 20"

def alert_bull_raging():
    settings = {
        "indicator_settings": {
            "apex_bull_raging": {
                "is_enabled": True,
            },
        },
        "recency": 5,
        "x": 20
    }

    overall_num_instances = 0
    overall_num_instances_rise = 0
    overall_change_percent = 0

    output_msg = ""

    for ticker in stock_list:
        print(f"Analyzing {ticker}")
        result = ie.analyze_stock(ticker, settings)
        if result is not None:
            overall_num_instances += result["total_instances"]
            overall_num_instances_rise += (
                result["total_instances"] * result["success_rate"] / 100
            )
            overall_change_percent += (
                result["total_instances"] * result["avg_percentage_change"]
            )

            if result["common_dates"] is not None:
                output_msg = f"{output_msg}\n✅ *{ticker}* - {result['common_dates'][-1]}"
                # Create a new DataFrame for the new row

    if output_msg == "":
        output_msg = "No stocks found matching the criteria"

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_msg = f""" *Bull raging screening completed at: {current_time}*
⚙️ Recency: {settings['recency']} days
{screening_pool_msg}

Win rate (stock rise) 20 days later(%): {round(overall_num_instances_rise/overall_num_instances*100, 2)}
Avg price change 20 days later(%): {round(overall_change_percent/overall_num_instances, 2)}
Number of times signal appear for everything scanned: {overall_num_instances}

Screen results (Ticker - Last Bull Raging Entry Date):

{output_msg}
"""
    tc.send_message(chat_id=27392018, message=output_msg)
    


def alert_bull_appear():
    settings = {
        "indicator_settings": {
            "apex_bull_appear": {
                "is_enabled": True,
            },
        },
        "recency": 5,
        "x": 20
    }

    overall_num_instances = 0
    overall_num_instances_rise = 0
    overall_change_percent = 0

    output_msg = ""

    for ticker in stock_list:
        print(f"Analyzing {ticker}")
        result = ie.analyze_stock(ticker, settings)
        if result is not None:
            overall_num_instances += result["total_instances"]
            overall_num_instances_rise += (
                result["total_instances"] * result["success_rate"] / 100
            )
            overall_change_percent += (
                result["total_instances"] * result["avg_percentage_change"]
            )

            if result["common_dates"] is not None:
                output_msg = f"{output_msg}\n✅ *{ticker}* - {result['common_dates'][-1]}"
                # Create a new DataFrame for the new row

    if output_msg == "":
        output_msg = "No stocks found matching the criteria"

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_msg = f""" *Bull appear screening completed at: {current_time}*
⚙️ Recency: {settings['recency']} days
{screening_pool_msg}

Win rate (stock rise) 20 days later(%): {round(overall_num_instances_rise/overall_num_instances*100, 2)}
Avg price change 20 days later(%): {round(overall_change_percent/overall_num_instances, 2)}
Number of times signal appear for everything scanned: {overall_num_instances}

Screen results (Ticker - Last Bull Appear Entry Date):
{output_msg}
"""

    tc.send_message(chat_id=27392018, message=output_msg)


if __name__ == "__main__":
    tc.send_message(chat_id=27392018, message="Started screening for bull appear..")
    alert_bull_appear()
    tc.send_message(chat_id=27392018, message="Started screening for bull raging..")
    alert_bull_raging()
    tc.send_message(chat_id=27392018, message="All scheduled screening completed!")
