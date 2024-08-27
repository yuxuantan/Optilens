

from controllers.tiger_controller import TigerController
import datetime
import streamlit as st
import pandas as pd
import utils
tc = TigerController()


# ===========  GET THE DATA ===========

filled_options_dict = tc.get_filled_orders('OPT', datetime.datetime.strptime('2019-01-01', '%Y-%m-%d').date())
filled_options_dict = [{
    'contract': order.contract,
    'qty_filled': -order.filled if order.action == 'SELL' else order.filled,
    'avg_fill_price': order.avg_fill_price,
    'trade_time': datetime.datetime.fromtimestamp(order.trade_time / 1000),
    'profit_usd': -(-order.filled if order.action == 'SELL' else order.filled) * order.avg_fill_price * 100
} for order in filled_options_dict]

filled_options_df = pd.DataFrame(filled_options_dict)
filled_options_df['contract'] = filled_options_df['contract'].astype(str)
filled_options_df.sort_values('trade_time', ascending=False, inplace=True)





# IF SAME contract OR (SAMEtrade_time_group GROUP, THEN SUM UP THE QTY FILLED, PROFIT USD, AND TRADE TIME
# filled_options_agg_df = filled_options_df.groupby('contract').agg({
    # 'avg_fill_price': 'last',
    # 'qty_filled': 'last',
    # 'trade_time': 'min',
    # 'profit_usd': 'sum',
# })
filled_options_agg_df = filled_options_df.groupby('contract').agg(
    opening_avg_fill_price = ('avg_fill_price', 'last'),
    opening_qty = ('qty_filled', 'last'),
    trade_time = ('trade_time', 'min'),
    profit_usd = ('profit_usd', 'sum'),
    net_qty_now = ('qty_filled', 'sum')
)
filled_options_agg_df.reset_index(inplace=True)
filled_options_agg_df[['symbol', 'expiry', 'strike', 'option_type']] = filled_options_agg_df['contract'].apply(lambda x: pd.Series(utils.parse_contract(x)))
# Group by time interval (e.g., 1 minute) to identify strategies
filled_options_agg_df['trade_time_group'] = filled_options_agg_df['trade_time'].dt.floor('T')

# Initialize the strategy column
filled_options_agg_df['strategy'] = 'Unknown'
filled_options_agg_df['strategy'] = filled_options_agg_df.groupby(['trade_time_group', 'symbol']).apply(utils.identify_strategy).reset_index(drop=True)

# Apply the capital calculation
filled_options_agg_df['capital_used'] = filled_options_agg_df.apply(utils.calculate_capital_used, axis=1)
# Calculate Return on Capital
filled_options_agg_df['Return on Capital (ROC) %'] = (filled_options_agg_df['profit_usd'] / filled_options_agg_df['capital_used']) * 100

# if net_qty_now !=0 then is_open = True, but if trade_time is before 2024, then is_open = False
filled_options_agg_df['is_open'] = (filled_options_agg_df['net_qty_now'] != 0) & (filled_options_agg_df['trade_time'] > datetime.datetime.strptime('2024-01-01', '%Y-%m-%d'))

# sort by trade time
filled_options_agg_df.sort_values('trade_time', ascending=False, inplace=True)




# ===========  DISPLAY THE CALCULATED HEADER METRICS ===========
col1, col2 = st.columns([1, 1])
with col1:
    st.header('Filled Options')
with col2:
    # add a button to clear cache st.cache_data.clear()
    if st.button('Refresh Data'):
        st.cache_data.clear()
        st.write('Cache cleared')
        st.rerun()

col1, col2, col3 = st.columns([1,1,1])
with col1:
    total_pnl = round(sum([data['profit_usd'] for data in filled_options_dict]), 2)
    # Calculate PnL change compared to 30 days ago
    pnl_change = round(total_pnl - utils.get_cumulative_sum_x_days_ago(filled_options_df, 30), 2)
    st.metric('Total Filled Options PnL', total_pnl, str(pnl_change) + ' USD in last 30 days')

      # ROC
    average_roc = filled_options_agg_df['Return on Capital (ROC) %'].mean()
    st.metric('Avg Return on Capital (%)', round(average_roc, 2))

with col2:
    win_rate = round(len(filled_options_agg_df[filled_options_agg_df['profit_usd'] > 0]) / len(filled_options_agg_df) * 100, 2)
    st.metric('Win Rate (%)', win_rate)

     # Profit Factor: The ratio of gross profit to gross loss, indicating overall profitability.
    gross_profit = filled_options_agg_df[filled_options_agg_df['profit_usd'] > 0]['profit_usd'].sum()
    gross_loss = filled_options_agg_df[filled_options_agg_df['profit_usd'] < 0]['profit_usd'].sum()
    profit_factor = gross_profit / abs(gross_loss) if gross_loss != 0 else 0
    st.metric('Profit Factor', round(profit_factor, 2))

with col3:
    # granularity
    selected_filter = st.selectbox(
        "View",
        ('Aggregated', 'All', 'Month on Month', 'Year on Year'),
    )

    # Maximum Drawdown: The largest drop from a peak to a trough in the Cumulative P&L (since there is no portfolio value for options trading)
    # calculate the running maximum of the cumulative P&L
    filled_options_agg_df['cumulative_profit'] = filled_options_agg_df['profit_usd'].cumsum()
    # calculate the drawdown (difference between the cumulative profit and the running maximum)
    filled_options_agg_df['drawdown'] = filled_options_agg_df['cumulative_profit'] - filled_options_agg_df['cumulative_profit'].cummax()
    # Calculate the drawdown percentage relative to the running maximum
    filled_options_agg_df['drawdown_pct'] = (filled_options_agg_df['drawdown'] / filled_options_agg_df['cumulative_profit'].cummax()) * 100
    #find the maximum drawdown
    max_drawdown = filled_options_agg_df['drawdown_pct'].min()
    st.metric('Max Drawdown of P&L (%)', round(max_drawdown, 2)) #value from -100 to 0, 0 means no drawdown


# ===========  DISPLAY THE DATA ===========



if selected_filter == 'Month on Month':
    col1, col2 = st.columns([1,2])
    with col1:
        # aggregate option p&l into a table with 2 columns --- month, total_pnl
        filled_options_month_df = filled_options_df.copy()
        filled_options_month_df['month'] = filled_options_month_df['trade_time'].dt.to_period('M')
        filled_options_month_df = filled_options_month_df.groupby('month')['profit_usd'].sum().reset_index()
        filled_options_month_df['month'] = filled_options_month_df['month'].astype(str)
        st.dataframe(filled_options_month_df.sort_values(by='month', ascending=False), hide_index=True)
    with col2:
        # show line chart of monthly p&l
        st.line_chart(filled_options_month_df, x='month', y='profit_usd')
elif selected_filter == 'Year on Year':
    filled_options_year_df = filled_options_df.copy()
    filled_options_year_df['year'] = filled_options_year_df['trade_time'].dt.to_period('Y')
    filled_options_year_df = filled_options_year_df.groupby('year')['profit_usd'].sum().reset_index()
    filled_options_year_df['year'] = filled_options_year_df['year'].astype(str)
    col1, col2 = st.columns([1,2])
    with col1:
        st.dataframe(filled_options_year_df.sort_values(by='year', ascending=False), hide_index=True)
    with col2:
        st.line_chart(filled_options_year_df, x='year', y='profit_usd')
elif selected_filter == 'Aggregated':    
    # display aggregated data
    st.subheader('Aggregated trade details')
    filled_options_agg_df = filled_options_agg_df[['contract', 'is_open', 'strategy', 'opening_avg_fill_price', 'opening_qty', 'trade_time', 'profit_usd', 'Return on Capital (ROC) %']]
    selected_row = st.dataframe(filled_options_agg_df, hide_index=True, selection_mode='single-row', on_select="rerun")

    # display selected trade details
    if len(selected_row['selection']['rows']) > 0:
        contract = filled_options_agg_df.iloc[selected_row['selection']['rows'][0]]['contract']
        st.subheader('Selected trade details')
        st.dataframe(filled_options_df[filled_options_df['contract'] == contract], hide_index=True)

elif selected_filter == 'All':
    st.dataframe(filled_options_df, hide_index=True)



