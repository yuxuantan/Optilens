

from archived.tiger_controller import TigerController
import datetime
import streamlit as st
import pandas as pd
import archived.utils as utils
tc = TigerController()

def options_insights_page(user_data):
    st.query_params.user_id = user_data['user']['user_id']
    # ===========  DISPLAY THE SIDEBAR ===========
    st.sidebar.title('Broker Configs')

    # create input for tiger credentials
    tiger_account = st.sidebar.text_input('Tiger Account', type='default')
    tiger_id = st.sidebar.text_input('Tiger ID', type='default')
    tiger_private_key = st.sidebar.text_input('Tiger Private Key', type='password')

    # ===========  GET THE DATA ===========

    options_dict = tc.get_orders('OPT', datetime.datetime.strptime('2019-01-01', '%Y-%m-%d').date())
    options_dict = [{
        'contract': order.contract,
        'qty_filled': -order.filled if order.action == 'SELL' else order.filled,
        'avg_fill_price': order.avg_fill_price,
        'trade_time': datetime.datetime.fromtimestamp(order.trade_time / 1000),
        'profit_usd': -(-order.filled if order.action == 'SELL' else order.filled) * order.avg_fill_price * 100
    } for order in options_dict]

    options_df = pd.DataFrame(options_dict)
    options_df['contract'] = options_df['contract'].astype(str)
    options_df.sort_values('trade_time', ascending=False, inplace=True)



    # IF SAME contract OR (SAMEtrade_time_group GROUP, THEN SUM UP THE QTY FILLED, PROFIT USD, AND TRADE TIME
    options_agg_df = options_df.groupby('contract').agg(
        opening_avg_fill_price = ('avg_fill_price', 'last'),
        opening_qty = ('qty_filled', 'last'),
        trade_time = ('trade_time', 'min'),
        profit_usd = ('profit_usd', 'sum'),
        net_qty_now = ('qty_filled', 'sum')
    )
    options_agg_df.reset_index(inplace=True)
    options_agg_df[['symbol', 'expiry', 'strike', 'option_type']] = options_agg_df['contract'].apply(lambda x: pd.Series(utils.parse_contract(x)))
    # Group by time interval (e.g., 1 minute) to identify strategies
    options_agg_df['trade_time_group'] = options_agg_df['trade_time'].dt.floor('T')

    # Initialize the strategy column
    options_agg_df['strategy'] = 'Unknown'
    options_agg_df['strategy'] = options_agg_df.groupby(['trade_time_group', 'symbol']).apply(utils.identify_strategy).reset_index(drop=True)

    # if net_qty_now !=0 then is_open = True, but if trade_time is before 2024, then is_open = False
    options_agg_df['is_open'] = (options_agg_df['net_qty_now'] != 0) & (options_agg_df['trade_time'] > datetime.datetime.strptime('2024-01-01', '%Y-%m-%d'))

    # sort by trade time
    options_agg_df.sort_values('trade_time', ascending=False, inplace=True)

    # filter out trades in the last 30 days and assign to another df - for change calculation
    options_agg_df_past = options_agg_df[options_agg_df['trade_time'] < datetime.datetime.now() - datetime.timedelta(days=30)]



    # ===========  DISPLAY THE CALCULATED HEADER METRICS ===========
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header('Optilens Dashboard')
    with col3:
        # add a button to clear cache st.cache_data.clear()
        if st.button('Refresh Data'):
            st.cache_data.clear()
            st.write('Cache cleared')
            st.rerun()
    # with col3:
        # granularity

    st.divider()


    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        total_pnl = round(sum([data['profit_usd'] for data in options_dict]), 2)
        # Calculate PnL change compared to 30 days ago
        pnl_change = round(total_pnl - utils.get_cumulative_sum_x_days_ago(options_df, 30), 2)
        st.metric('Total Options PnL (USD)', total_pnl, str(pnl_change) + ' in last mth')
        # ROC
        avg_roc, avg_roc_change = utils.get_return_on_capital(options_agg_df, options_agg_df_past)
        st.metric('Avg Return on Capital (%)', round(avg_roc, 2), str(round(avg_roc_change, 2)) + ' in last mth')

    with col2:
        win_rate, win_rate_change = utils.get_win_rate(options_agg_df, options_agg_df_past)
        st.metric('Win Rate (%)', win_rate, str(win_rate_change)+' in last mth')

        profit_factor, profit_factor_change = utils.get_profit_factor(options_agg_df, options_agg_df_past)
        st.metric('Profit Factor', round(profit_factor, 2), str(round(profit_factor_change, 2)) + ' in last mth')

    with col3:
        max_drawdown, max_drawdown_change = utils.get_max_drawdown_pnl(options_agg_df, options_agg_df_past)
        st.metric('Max Drawdown of P&L (%)', round(max_drawdown, 2), str(round(max_drawdown_change, 2)) + ' in last mth') #value from -100 to 0, 0 means no drawdown
        st.metric('Sharpe Ratio', round(utils.get_sharpe_ratio(options_df), 2))


    st.divider()
    # ===========  DISPLAY THE DATA ===========
    col1, col2 = st.columns([3, 1])
    with col1:
        st.empty()
    with col2:
        selected_filter = st.selectbox(
            "View",
            ('Aggregated', 'All', 'Month on Month', 'Year on Year'),
        )
    if selected_filter == 'Month on Month':
        st.subheader('Monthly trade profit')
        col1, col2 = st.columns([1,2])
        with col1:
            # aggregate option p&l into a table with 2 columns --- month, total_pnl
            options_month_df = options_df.copy()
            options_month_df['month'] = options_month_df['trade_time'].dt.to_period('M')
            options_month_df = options_month_df.groupby('month')['profit_usd'].sum().reset_index()
            options_month_df['month'] = options_month_df['month'].astype(str)
            st.dataframe(options_month_df.sort_values(by='month', ascending=False), hide_index=True)
        with col2:
            # show line chart of monthly p&l
            st.line_chart(options_month_df, x='month', y='profit_usd')
    elif selected_filter == 'Year on Year':
        st.subheader('Yearly trade profit')
        options_year_df = options_df.copy()
        options_year_df['year'] = options_year_df['trade_time'].dt.to_period('Y')
        options_year_df = options_year_df.groupby('year')['profit_usd'].sum().reset_index()
        options_year_df['year'] = options_year_df['year'].astype(str)
        col1, col2 = st.columns([1,2])
        with col1:
            st.dataframe(options_year_df.sort_values(by='year', ascending=False), hide_index=True)
        with col2:
            st.line_chart(options_year_df, x='year', y='profit_usd')
    elif selected_filter == 'Aggregated':
        # display aggregated data
        st.subheader('Aggregated trade details')
        options_agg_df = options_agg_df[['contract', 'is_open', 'strategy', 'opening_avg_fill_price', 'opening_qty', 'trade_time', 'profit_usd', 'Return on Capital (ROC) %']]
        selected_row = st.dataframe(options_agg_df, hide_index=True, selection_mode='single-row', on_select="rerun")

        # display selected trade details
        if len(selected_row['selection']['rows']) > 0:
            contract = options_agg_df.iloc[selected_row['selection']['rows'][0]]['contract']
            st.subheader('Selected trade details')
            st.dataframe(options_df[options_df['contract'] == contract], hide_index=True)

    elif selected_filter == 'All':
        st.subheader('All trades')
        st.dataframe(options_df, hide_index=True)



