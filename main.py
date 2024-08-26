

from controllers.tiger_controller import TigerController
import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import utils

tc = TigerController()
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

opt_col1, opt_col2 = st.columns([2,1])

with opt_col1:
    st.subheader('Filled Options')
with opt_col2:
    # granularity
    option = st.selectbox(
        "View",
        ('All', 'Month on Month', 'Year on Year'),
    )

total_pnl = round(sum([data['profit_usd'] for data in filled_options_data]), 2)
filled_options_df = pd.DataFrame(filled_options_data)
# Calculate PnL change compared to 30 days ago
pnl_change = round(total_pnl - utils.get_cumulative_sum_x_days_ago(filled_options_df, 30), 2)
st.metric('Total Filled Options PnL', total_pnl, pnl_change)

filled_options_month_df = filled_options_df.copy()
filled_options_month_df['month'] = filled_options_month_df['trade_time'].dt.to_period('M')
filled_options_month_df = filled_options_month_df.groupby('month')['profit_usd'].sum().reset_index()
filled_options_month_df['month'] = filled_options_month_df['month'].astype(str)

filled_options_year_df = filled_options_df.copy()
filled_options_year_df['year'] = filled_options_year_df['trade_time'].dt.to_period('Y')
filled_options_year_df = filled_options_year_df.groupby('year')['profit_usd'].sum().reset_index()
filled_options_year_df['year'] = filled_options_year_df['year'].astype(str)

if option == 'Month on Month':
    col1, col2 = st.columns([1,2])
    # aggregate option p&l into a table with 2 columns --- month, total_pnl
    with col1:
        st.dataframe(filled_options_month_df.sort_values(by='month', ascending=False), hide_index=True)
    # show line chart of monthly p&l
    with col2:
        st.line_chart(filled_options_month_df, x='month', y='profit_usd')
elif option == 'Year on Year':
    col1, col2 = st.columns([1,2])
    with col1:
        st.dataframe(filled_options_year_df.sort_values(by='year', ascending=False), hide_index=True)
    with col2:
        st.line_chart(filled_options_year_df, x='year', y='profit_usd')
else:    
    # display data normally
    st.dataframe(filled_options_df.sort_values(by='trade_time', ascending=False), hide_index=True)


