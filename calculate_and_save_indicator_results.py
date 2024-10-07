import utils.ticker_getter as tg
import utils.indicator_evaluator as ie
import utils.supabase as db

def calculate_and_save_indicator_results():
    stock_list = tg.get_all_tickers()
    # fetch all tickers
    # fetch from supabase db and filter out those that already have updated values
    apex_bull_appear_cache = db.fetch_cached_data_from_supabase('apex_bull_appear')
    apex_bull_raging_cache = db.fetch_cached_data_from_supabase('apex_bull_raging')
    apex_bear_appear_cache = db.fetch_cached_data_from_supabase('apex_bear_appear')

    # if the created_at date is after 5am SGT, then it should be removed
    def filter_tickers(cache, description):
        filtered_tickers = [
            ticker['ticker'] for ticker in cache
            if ticker['created_at'] > '05:00:00' and ticker['analysis']
        ]
        print(f"Tickers no need to screen {description}: {len(filtered_tickers)}")
        return list(set(stock_list) - set(filtered_tickers))

    tickers_to_screen_bull_appear = filter_tickers(apex_bull_appear_cache, 'bull appear')
    tickers_to_screen_bull_raging = filter_tickers(apex_bull_raging_cache, 'bull raging')
    tickers_to_screen_bear_appear = filter_tickers(apex_bear_appear_cache, 'bear appear')
    
    # print number to screen for each indicator 
    print(f"Tickers to screen for bull appear: {len(tickers_to_screen_bull_appear)}")
    print(f"Tickers to screen for bull raging: {len(tickers_to_screen_bull_raging)}")
    print(f"Tickers to screen for bear appear: {len(tickers_to_screen_bear_appear)}")

    total_tickers_to_screen = len(set(tickers_to_screen_bull_appear + tickers_to_screen_bull_raging + tickers_to_screen_bear_appear))
    tickers_screened = 0
    tickers_screened_bull_appear = 0
    tickers_screened_bull_raging = 0
    tickers_screened_bear_appear = 0

    # for each ticker, calculate the indicator results and upsert to db
    for ticker in set(tickers_to_screen_bull_appear + tickers_to_screen_bull_raging + tickers_to_screen_bear_appear):
        data = tg.fetch_stock_data(ticker)
        
        if ticker in tickers_to_screen_bull_appear:
            dates_bull_appear = ie.get_apex_bull_appear_dates(data)
            analysis_result_bull_appear = get_analysis_results(dates_bull_appear, data)
            db.upsert_data_to_supabase('apex_bull_appear', {'ticker': ticker, 'analysis': analysis_result_bull_appear, 'created_at': 'now()'})
            print(f"Upserted bull appear analysis for {ticker}")
            tickers_screened_bull_appear += 1

        if ticker in tickers_to_screen_bull_raging:
            dates_bull_raging = ie.get_apex_bull_raging_dates(data)
            analysis_result_bull_raging = get_analysis_results(dates_bull_raging, data)
            db.upsert_data_to_supabase('apex_bull_raging', {'ticker': ticker, 'analysis': analysis_result_bull_raging, 'created_at': 'now()'})
            print(f"Upserted bull raging analysis for {ticker}")
            tickers_screened_bull_raging += 1
        
        if ticker in tickers_to_screen_bear_appear:
            dates_bear_appear = ie.get_apex_bear_appear_dates(data)
            analysis_result_bear_appear = get_analysis_results(dates_bear_appear, data)
            db.upsert_data_to_supabase('apex_bear_appear', {'ticker': ticker, 'analysis': analysis_result_bear_appear, 'created_at': 'now()'})
            print(f"Upserted bear appear analysis for {ticker}")
            tickers_screened_bear_appear += 1

        tickers_screened += 1
        print(f"Progress: {tickers_screened}/{total_tickers_to_screen} tickers screened")
        print(f"Progress for bull appear: {tickers_screened_bull_appear}/{len(tickers_to_screen_bull_appear)} tickers screened")
        print(f"Progress for bull raging: {tickers_screened_bull_raging}/{len(tickers_to_screen_bull_raging)} tickers screened")
        print(f"Progress for bear appear: {tickers_screened_bear_appear}/{len(tickers_to_screen_bear_appear)} tickers screened")

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
    
calculate_and_save_indicator_results()