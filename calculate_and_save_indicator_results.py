import utils.ticker_getter as tg
import utils.indicator_evaluator as ie
import utils.supabase as db
import pandas as pd
import numpy as np

def calculate_and_save_indicator_results():
    stock_list = tg.get_all_tickers()
    apex_bull_appear_cache = db.fetch_cached_data_from_supabase('apex_bull_appear')
    apex_bull_raging_cache = db.fetch_cached_data_from_supabase('apex_bull_raging')
    apex_bear_appear_cache = db.fetch_cached_data_from_supabase('apex_bear_appear')
    apex_bear_raging_cache = db.fetch_cached_data_from_supabase('apex_bear_raging')

    def filter_tickers(cache, description):
        filtered_tickers = [
            ticker['ticker'] for ticker in cache
            if ticker['created_at'] > '05:00:00'
        ]
        print(f"Tickers no need to screen {description}: {len(filtered_tickers)}")
        return list(set(stock_list) - set(filtered_tickers))

    tickers_to_screen = {
        'bull_appear': filter_tickers(apex_bull_appear_cache, 'bull appear'),
        'bull_raging': filter_tickers(apex_bull_raging_cache, 'bull raging'),
        'bear_appear': filter_tickers(apex_bear_appear_cache, 'bear appear'),
        'bear_raging': filter_tickers(apex_bear_raging_cache, 'bear raging')
    }

    for key, tickers in tickers_to_screen.items():
        print(f"Tickers to screen for {key.replace('_', ' ')}: {len(tickers)}")

    total_tickers_to_screen = len(set(sum(tickers_to_screen.values(), [])))
    tickers_screened = {key: 0 for key in tickers_to_screen}
    tickers_screened_total = 0

    def process_ticker(ticker, indicator, get_dates_func, table_name):
        dates = get_dates_func(ticker_data)
        analysis_result = get_analysis_results(dates, ticker_data)
        analysis_result = convert_to_serializable(analysis_result)
        if analysis_result:
            try:
                db.upsert_data_to_supabase(table_name, {'ticker': ticker, 'analysis': analysis_result, 'created_at': 'now()'})
                print(f"Upserted {indicator} analysis for {ticker}")
            except Exception as e:
                print(f"❌ Failed to upsert {indicator} analysis for {ticker}: {e}")
            print(f"Upserted {indicator} analysis for {ticker}")
        else:
            print(f"No {indicator} analysis to upsert for {ticker}")
        tickers_screened[indicator] += 1

    for ticker in set(sum(tickers_to_screen.values(), [])):
        ticker_data = tg.fetch_stock_data(ticker)

        if ticker in tickers_to_screen['bull_appear']:
            process_ticker(ticker, 'bull_appear', ie.get_apex_bull_appear_dates, 'apex_bull_appear')

        if ticker in tickers_to_screen['bull_raging']:
            process_ticker(ticker, 'bull_raging', ie.get_apex_bull_raging_dates, 'apex_bull_raging')

        if ticker in tickers_to_screen['bear_appear']:
            process_ticker(ticker, 'bear_appear', ie.get_apex_bear_appear_dates, 'apex_bear_appear')
        
        if ticker in tickers_to_screen['bear_raging']:
            process_ticker(ticker, 'bear_raging', ie.get_apex_bear_raging_dates, 'apex_bear_raging')

        tickers_screened_total += 1
        print(f"Progress: {tickers_screened_total}/{total_tickers_to_screen} tickers screened")
        for key, count in tickers_screened.items():
            print(f"Progress for {key.replace('_', ' ')}: {count}/{len(tickers_to_screen[key])} tickers screened")

def get_analysis_results(dates, data):
    analysis_results = {}
    if dates is None:
        return analysis_results
    
    for date in dates:
        date_index = data.index.get_loc(date)
        if date_index != -1:
            date_str = date.strftime('%Y-%m-%d')
            analysis_results[date_str] = {}
            analysis_results[date_str]['change1TD'] = ((data.iloc[date_index + 1]['Close'] - data.iloc[date_index]['Close']) / data.iloc[date_index]['Close']) * 100 if date_index + 1 < len(data) else None
            analysis_results[date_str]['change5TD'] = ((data.iloc[date_index + 5]['Close'] - data.iloc[date_index]['Close']) / data.iloc[date_index]['Close']) * 100 if date_index + 5 < len(data) else None
            analysis_results[date_str]['change20TD'] = ((data.iloc[date_index + 20]['Close'] - data.iloc[date_index]['Close']) / data.iloc[date_index]['Close']) * 100 if date_index + 20 < len(data) else None
            analysis_results[date_str]['volume'] = data.iloc[date_index]['Volume']
            analysis_results[date_str]['close'] = data.iloc[date_index]['Close']
    
    return analysis_results

def convert_to_serializable(data):
    if isinstance(data, dict):
        return {k: convert_to_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_to_serializable(i) for i in data]
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif isinstance(data, np.int64):
        return int(data)
    elif isinstance(data, np.float64):
        return float(data)
    else:
        return data

calculate_and_save_indicator_results()
