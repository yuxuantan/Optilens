from tigeropen.trade.trade_client import TradeClient
from tigeropen.tiger_open_config import TigerOpenClientConfig
from tigeropen.common.consts import SecurityType, Market
import datetime
import streamlit as st
class TigerController:
    def __init__(self):
        self.trade_client = self.create_trade_client()

    def create_trade_client(self):
        config = TigerOpenClientConfig(sandbox_debug=None, enable_dynamic_domain=True,props_path=None)
        config.private_key = st.secrets['TIGER_PRIVATE_KEY']
        config.account = st.secrets['TIGER_ACCOUNT']
        config.tiger_id = st.secrets['TIGER_ID']
        trade_client = TradeClient(config)
        return trade_client

    def get_filled_orders(self, sec_type = SecurityType.ALL, start_date = datetime.datetime.now()-datetime.timedelta(days=30), end_date = datetime.datetime.now().date()):

        date_diff_days = (end_date - start_date).days
        print("date_diff_days: " + str(date_diff_days))
        # check if start_time and end_time is more than 3 months
        if date_diff_days > 90:
            # split the date range into multiple api calls with 3 months each, and return accumulated results
            filled_orders = []
            for i in range(0, date_diff_days, 90):
                segment_start_date = start_date + datetime.timedelta(days=i)
                segment_end_date = start_date + datetime.timedelta(days=i+90)
                print("segment_start_date: " + str(segment_start_date))
                print("segment_end_date: " + str(segment_end_date))
                orders = self.trade_client.get_filled_orders(sec_type=sec_type, start_time=str(segment_start_date), end_time=str(segment_end_date))
                filled_orders.extend(orders)
                print("filled_order_count: " + str(len(filled_orders)))
        else:
            filled_orders = self.trade_client.get_filled_orders(sec_type=sec_type, start_time=str(start_date), end_time=str(end_date))
            
        # sort filled orders by trade_time
        filled_orders.sort(key=lambda x: x.trade_time, reverse=True)
        return filled_orders

    def get_open_positions(self):
        open_positions = self.trade_client.get_positions()
        return open_positions

        
        


if __name__ == "__main__":
    controller = TigerController()
    filled_orders = controller.get_filled_orders()