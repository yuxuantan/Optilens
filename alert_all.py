from datetime import datetime, timedelta
import utils.telegram_controller as tc
import utils.supabase as db

chat_ids = [
    27392018,  # me
    # 432502167 # rainbow
]

def alert(indicator_name):
    # Fetch cached data for the given indicator
    bull_raging_cache = db.fetch_cached_data_from_supabase(indicator_name)

    # Filter out data with 'analysis' column's last JSON key older than 5 days
    five_days_ago = datetime.now() - timedelta(days=6)

    results_output = "__ *ticker | entry date | close price | volume* __\n"

    # Filter and format the data
    filtered_tickers = []
    for ticker in bull_raging_cache:
        last_key = next(reversed(ticker["analysis"]), None)
        if last_key:
            last_key_date = datetime.strptime(last_key, '%Y-%m-%d')
            if last_key_date > five_days_ago:
                filtered_tickers.append(ticker)
                ticker_symbol = ticker.get('ticker', '?')
                entry_date = last_key if last_key else '?'
                entry_close_price = ticker['analysis'][last_key].get('close', '?')
                volume = ticker['analysis'][last_key].get('volume', '?')

                # Format entry close price and volume
                if entry_close_price != '?':
                    entry_close_price = round(float(entry_close_price), 2)

                if volume != '?':
                    volume = round(float(volume))

                if entry_close_price == '?' or volume == '?' or entry_close_price < 20 or volume < 1000000:
                    continue

                # Add row to the table
                results_output += f"✅ *{ticker_symbol}* | {entry_date} | {entry_close_price} | {volume}\n"

    # Check if there are results
    if not filtered_tickers:
        return f"*{indicator_name} screening completed*\n\n⚙️ Close price > 20, Volume > 100k\n\nNo stocks found matching the criteria"

    # Use PrettyTable's string representation to create the message

    output_msg = f"""*{indicator_name} screening completed*\n\n⚙️ Close price > 20, Volume > 100k \n\n *Screen results:*\n{results_output}"""
    
    return output_msg


if __name__ == "__main__":
    # Send messages for each indicator
    tc.send_message(chat_ids, message=alert('apex_bull_raging'))
    tc.send_message(chat_ids, message=alert('apex_bull_appear'))
