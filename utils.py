
import datetime
def get_cumulative_sum_x_days_ago(df, x_days_ago, time_col='trade_time', value_col='profit_usd'):
    today_date = datetime.datetime.now().date()
    x_days_ago_date = today_date - datetime.timedelta(days=x_days_ago)
    x_days_ago_sum = df[df[time_col].dt.date <= x_days_ago_date][value_col].sum()
    return x_days_ago_sum