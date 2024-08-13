
from controllers.gsheet_controller import GsheetController
import datetime
from controllers.tiger_controller import TigerController

gc = GsheetController()
tc = TigerController()

def get_filled_options():
    filled_orders = tc.get_filled_orders('OPT', datetime.datetime.strptime('2024-01-01', '%Y-%m-%d').date())

    gc.clearAllDataAndRepopulateHeader('FilledOptions', ['contract', 'qty_filled', 'avg_fill_price', 'trade_time', 'profit'])

    total_profit = 0
    for order in filled_orders:
        trade_time = datetime.datetime.fromtimestamp(order.trade_time / 1000)
        qty_filled = order.filled
        if order.action == 'SELL':
            qty_filled = -qty_filled
        profit = -qty_filled * order.avg_fill_price * 100
        total_profit += profit
        gc.writeRow([str(order.contract), qty_filled, order.avg_fill_price, str(trade_time), profit], 'FilledOptions')

    gc.writeRow(['Total Options Profit', total_profit], 'FilledOptions')
    


def get_filled_stocks():
    gc.clearAllDataAndRepopulateHeader('FilledStocks', ['contract', 'qty_filled', 'avg_fill_price', 'trade_time', 'profit'])
    filled_orders = tc.get_filled_orders('STK', datetime.datetime.strptime('2024-01-01', '%Y-%m-%d').date())
    total_profit = 0
    for order in filled_orders:
        trade_time = datetime.datetime.fromtimestamp(order.trade_time / 1000)
        qty_filled = order.filled
        if order.action == 'SELL':
            qty_filled = -qty_filled
        total_profit += order.realized_pnl
        gc.writeRow([str(order.contract), qty_filled, order.avg_fill_price, str(trade_time), order.realized_pnl], 'FilledStocks')
    gc.writeRow(['Total Stocks Profit', total_profit], 'FilledStocks')
    
    
def get_open_positions():
    gc.clearAllDataAndRepopulateHeader('OpenPositions', ['contract', 'quantity', 'average_cost', 'market_price', 'pnl'])
    open_positions = tc.get_open_positions()
    total_pnl = 0
    for position in open_positions:
        pnl = position.market_price * position.quantity - position.average_cost * position.quantity
        gc.writeRow([str(position.contract), position.quantity, position.average_cost, position.market_price, pnl], 'OpenPositions')
        total_pnl += pnl
    gc.writeRow(['Total PnL', total_pnl], 'OpenPositions')
    
    
    
if __name__ == "__main__":
    # get_filled_options()
    # get_filled_stocks()
    get_open_positions()