# import yfinance as yf
import ticker_getter as tg
import pandas as pd


def get_2day_aggregated_data(data):
    # Ensure the Date column is the index and is of datetime type
    data.index = pd.to_datetime(data.index)

    # if there is odd number of data points, drop the first row in the aggregate calculation
    if len(data) % 2 == 1:
        data = data.iloc[1:]

    # Group data into 2-day periods of price movement (2-day chart)
    grouped = data[['High', 'Low', 'Open', 'Close']].rolling(window=2, min_periods=1).agg({
        'High': 'max',
        'Low': 'min',
        'Open': lambda x: x.iloc[0],
        'Close': lambda x: x.iloc[-1]
    })
    aggregated_data = grouped.shift(-1).iloc[::2]
    return aggregated_data


 # step 1: get all the inflexion points in the data (where T-1 < T > T+1 or T-1 > T < T+1)
data = tg.fetch_stock_data('AAPL', period='1y', interval='1d')

data = get_2day_aggregated_data(data)

high_inflexion_points = []
low_inflexion_points = []
for i in range(1, len(data)-1):
    if (data['High'][i-1] < data['High'][i] > data['High'][i+1]):
        high_inflexion_points.append(data.index[i])
    elif (data['Low'][i-1] > data['Low'][i] < data['Low'][i+1]):
        low_inflexion_points.append(data.index[i])

inflexion_points = sorted(high_inflexion_points + low_inflexion_points)

inflexion_data = data.loc[inflexion_points, ['High', 'Low']]
inflexion_data = pd.DataFrame(inflexion_data)


lightning = []

# GROUP of 4 inflexion points
for inflexion_point in high_inflexion_points:
    # get index of inflexion point
    inflexion_point_pos = inflexion_data.index.get_loc(inflexion_point)
    # if inflexion point is one of the last 4 datapoints, skip
    if inflexion_point_pos >= len(inflexion_data)-4:
        break

    # Get price of first inflexion point
    price_a_high = inflexion_data.iloc[inflexion_point_pos]['High']
    price_b_high = inflexion_data.iloc[inflexion_point_pos+1]['High']
    price_b_low = inflexion_data.iloc[inflexion_point_pos+1]['Low']
    price_c_high = inflexion_data.iloc[inflexion_point_pos+2]['High']
    price_c_low = inflexion_data.iloc[inflexion_point_pos+2]['Low']
    price_d_high = inflexion_data.iloc[inflexion_point_pos+3]['High']
    price_d_low = inflexion_data.iloc[inflexion_point_pos+3]['Low']

    # Check for lightning. must start with high inflexion point, C must be lower than A ,   D must be lower than B and cross back to B (assume it just have to reverse in the direction, but havent reach B)
    if price_c_high < price_a_high and price_d_low < price_b_low:
        # add all the dateindex of 4 inflexion points abcd
        lightning.append([inflexion_point, inflexion_data.index[inflexion_point_pos+1], inflexion_data.index[inflexion_point_pos+2], inflexion_data.index[inflexion_point_pos+3]])


for formation in lightning:
    print(formation)


    # For M
    # D must be higher than  B and cross back to C to reach E (above A)

    # Note that uptrend formation must form above sma50 line & sma200. 

# print(inflexion_points)