import utils.indicator_evaluator as ie
import utils.ticker_getter as tg

data = tg.fetch_stock_data('AAPL')
print(ie.get_apex_bear_raging_dates(data))