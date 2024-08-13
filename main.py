

from controllers.tiger_controller import TigerController
import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from controllers.crypto_controller import get_wallet_token_balances_price
from controllers.cb_controller import get_coinbase_balance

tc = TigerController()

sideb = st.sidebar
crypto_wallet_labels = []
crypto_wallet_addresses = []

crypto_wallets = {}

crypto_wallet_address1 = sideb.text_input('Crypto wallet 1 address', '0x42490ba4d1ab3dc1a0780e18fdc3b900059e9966')
crypto_wallet_label1 = sideb.text_input('Crypto wallet 1 label', 'Wallet 1')
if crypto_wallet_label1 and crypto_wallet_address1:
    crypto_wallets[crypto_wallet_address1] = crypto_wallet_label1

crypto_wallet_address2 = sideb.text_input('Crypto wallet 2 address', '0x26f36257245FF5E86024370A51e17Df7a4c1eF77')
crypto_wallet_label2 = sideb.text_input('Crypto wallet 2 label', 'Wallet 2')
if crypto_wallet_label2 and crypto_wallet_address2:
    crypto_wallets[crypto_wallet_address2] = crypto_wallet_label2

crypto_wallet_labels = list(crypto_wallets.values())
crypto_wallet_addresses = list(crypto_wallets.keys())



st.title('Neural Nexus')
open_pos_stks_tab, open_pos_crypto_tab, filled_opt_tab, filled_stk_tab = st.tabs(["Open Position Stocks", "Open Position Crypto", "Filled Options", "Filled Stocks"])



# ========= OPEN POSITIONS STOCKS TAB =========
open_pos_stks_tab.subheader('Open Positions Stocks')

# get the data
open_positions = tc.get_open_positions()
open_positions_data = [{
    'contract': position.contract,
    'quantity': position.quantity,
    'average_cost': round(position.average_cost, 2),
    'market_price': round(position.market_price, 2),
    'market_value': position.market_price * position.quantity,
    'pnl': position.market_price * position.quantity - position.average_cost * position.quantity
} for position in open_positions]

total_pnl = round(sum([position['pnl'] for position in open_positions_data]), 2)
total_market_value = round(sum([position['market_value'] for position in open_positions_data]), 2)

# write the data
col1, col2, col3, col4 = open_pos_stks_tab.columns([1, 1, 1, 1])
col1.metric('Unrealised PnL', total_pnl)
col2.metric('Total Market Value', total_market_value)

open_pos_stks_tab.dataframe(pd.DataFrame(open_positions_data), hide_index=True)

# plot the pie chart of open positions
labels = [position['contract'] for position in open_positions_data]
sizes = [position['market_value'] for position in open_positions_data]
fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
ax1.axis('equal')
open_pos_stks_tab.pyplot(fig1)


# ========= OPEN POSITIONS CRYPTO TAB =========
# crypto
open_pos_crypto_tab.subheader('Open Positions Crypto')

crypto_balances_df = pd.DataFrame(get_wallet_token_balances_price(crypto_wallet_addresses))
crypto_balances_df['wallet_label'] = crypto_balances_df['wallet_address'].map(crypto_wallets)
total_market_value = round(crypto_balances_df['usd_value'].sum(), 2)
open_pos_crypto_tab.metric('Total Market Value', total_market_value)
open_pos_crypto_tab.dataframe(crypto_balances_df[['wallet_label', 'chain', 'symbol', 'balance', 'usd_price', 'usd_value']], hide_index=True)


coinbase_balances_df = pd.DataFrame(get_coinbase_balance())
total_market_value_coinbase = round(coinbase_balances_df['usd_value'].sum(), 2)
open_pos_crypto_tab.metric('Total Market Value Coinbase', total_market_value_coinbase)
open_pos_crypto_tab.dataframe(coinbase_balances_df, hide_index=True)
# ===========  FILLED OPTIONS TAB ===========

# get data
filled_options = tc.get_filled_orders('OPT', datetime.datetime.strptime('2020-01-01', '%Y-%m-%d').date())
filled_options_data = [{
    'contract': order.contract,
    'qty_filled': -order.filled if order.action == 'SELL' else order.filled,
    'avg_fill_price': order.avg_fill_price,
    'trade_time': datetime.datetime.fromtimestamp(order.trade_time / 1000),
    'profit_usd': -(-order.filled if order.action == 'SELL' else order.filled) * order.avg_fill_price * 100
} for order in filled_options]

opt_col1, opt_col2 = filled_opt_tab.columns([2,1])

with opt_col1:
    st.subheader('Filled Options')
with opt_col2:
    # granularity
    option = st.selectbox(
        "View",
        ('All', 'Month on Month', 'Year on Year'),
    )

total_pnl = round(sum([data['profit_usd'] for data in filled_options_data]), 2)
filled_opt_tab.metric('Total Filled Options PnL', total_pnl)
filled_options_df = pd.DataFrame(filled_options_data)

filled_options_month_df = filled_options_df.copy()
filled_options_month_df['month'] = filled_options_month_df['trade_time'].dt.to_period('M')
filled_options_month_df = filled_options_month_df.groupby('month')['profit_usd'].sum().reset_index()
filled_options_month_df['month'] = filled_options_month_df['month'].astype(str)

filled_options_year_df = filled_options_df.copy()
filled_options_year_df['year'] = filled_options_year_df['trade_time'].dt.to_period('Y')
filled_options_year_df = filled_options_year_df.groupby('year')['profit_usd'].sum().reset_index()
filled_options_year_df['year'] = filled_options_year_df['year'].astype(str)

if option == 'Month on Month':
    col1, col2 = filled_opt_tab.columns([1,2])
    # aggregate option p&l into a table with 2 columns --- month, total_pnl
    with col1:
        st.dataframe(filled_options_month_df.sort_values(by='month', ascending=False), hide_index=True)
    # show line chart of monthly p&l
    with col2:
        st.line_chart(filled_options_month_df, x='month', y='profit_usd')
elif option == 'Year on Year':
    col1, col2 = filled_opt_tab.columns([1,2])
    with col1:
        st.dataframe(filled_options_year_df.sort_values(by='year', ascending=False), hide_index=True)
    with col2:
        st.line_chart(filled_options_year_df, x='year', y='profit_usd')
else:    
    # display data normally
    filled_opt_tab.dataframe(filled_options_df.sort_values(by='trade_time', ascending=False), hide_index=True)




# ========== FILLED STOCKS TAB ============
filled_stocks = tc.get_filled_orders('STK', datetime.datetime.strptime('2020-01-01', '%Y-%m-%d').date())
filled_stocks_data = [{
    'contract': order.contract,
    'qty_filled': -order.filled if order.action == 'SELL' else order.filled,
    'avg_fill_price': round(order.avg_fill_price, 2),
    'trade_time': datetime.datetime.fromtimestamp(order.trade_time / 1000),
    'profit_usd': round(order.realized_pnl, 2)
} for order in filled_stocks]


stk_col1, stk_col2 = filled_stk_tab.columns([2,1])
with stk_col1:
    st.subheader('Filled Stocks')
with stk_col2: 
    option2 = st.selectbox(
        "View",
        ('All', 'Month on Month', 'Year on Year'),
        key='option2'
    )

total_pnl = round(sum([data['profit_usd'] for data in filled_stocks_data]), 2)
filled_stk_tab.metric('Total Filled Stocks PnL', total_pnl)
filled_stocks_df = pd.DataFrame(filled_stocks_data)

col1, col2 = filled_stk_tab.columns([1,2])

filled_stocks_month_df = filled_stocks_df.copy()
filled_stocks_month_df['month'] = filled_stocks_month_df['trade_time'].dt.to_period('M')
filled_stocks_month_df = filled_stocks_month_df.groupby('month')['profit_usd'].sum().reset_index()
filled_stocks_month_df['month'] = filled_stocks_month_df['month'].astype(str)

filled_stocks_year_df = filled_stocks_df.copy()
filled_stocks_year_df['year'] = filled_stocks_year_df['trade_time'].dt.to_period('Y')
filled_stocks_year_df = filled_stocks_year_df.groupby('year')['profit_usd'].sum().reset_index()
filled_stocks_year_df['year'] = filled_stocks_year_df['year'].astype(str)

if option2 == 'Month on Month':
    with col1:
        st.dataframe(filled_stocks_month_df.sort_values(by='month', ascending=False), hide_index=True)
    with col2:
        st.line_chart(filled_stocks_month_df, x='month', y='profit_usd')
elif option2 == 'Year on Year':
    with col1:
        st.dataframe(filled_stocks_year_df.sort_values(by='year', ascending=False), hide_index=True)
    with col2:
        st.line_chart(filled_stocks_year_df, x='year', y='profit_usd')
else:
    filled_stk_tab.dataframe(filled_stocks_df.sort_values(by='trade_time', ascending=False), hide_index=True)
