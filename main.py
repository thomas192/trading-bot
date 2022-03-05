import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime


def ema(df, name, n):
    price = df["close"]
    price.fillna(method='ffill', inplace=True)
    price.fillna(method='bfill', inplace=True)
    # ema = pd.Series(price.ewm(span=n, min_periods=n).mean(), name='EMA_{}'.format(n))
    # df = df.join(ema)
    df[name] = price.ewm(span=n, min_periods=n).mean()
    return df


BTCUSDT = 'BTC/USDT'

# collect candlestick data from Binance
binance = ccxt.binance()
binance.load_markets()
# print(binance.symbols)
candles = binance.fetchOHLCV(symbol=BTCUSDT, timeframe='1d', since=binance.parse8601("2020-01-01T00:00:00"))

# format date
for candle in candles:
    candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

# create dataframe
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]

# add indicators to dataframe
short_span = 10
long_span = 20
chart = ema(chart, "short_ema", short_span)
chart = ema(chart, "long_ema", long_span)
# df['short_ema'] = df['close'].ewm(span=20, min_periods=20).mean()

# strategy
strategy = pd.DataFrame(chart["date"])
strategy["order"] = ""
strategy["price"] = np.nan
positioned = False
for index, row in chart.iterrows():
    if chart["short_ema"][index] > chart["long_ema"][index] and positioned is False:
        strategy.at[index+1, "order"] = "buy"
        strategy.at[index+1, "price"] = chart["open"][index]
        positioned = True
    if chart["short_ema"][index] < chart["long_ema"][index] and positioned is True:
        strategy.at[index+1, "order"] = "sell"
        strategy.at[index + 1, "price"] = chart["open"][index]
        positioned = False


# print(strategy.iloc[np.where(strategy.order.values == "sell")])
# print(strategy[strategy["order"] == "buy"].count())
# print(strategy[strategy["order"] == "sell"].count())
# df["buy"][df.short_ema > df.long_ema] = 1

# make plot
dfinal = pd.merge(chart, strategy, on="date", how="left")
plt.plot(dfinal["close"])
plt.plot(dfinal["short_ema"], color="y")
plt.plot(dfinal["long_ema"], color="m")
plt.scatter(x=dfinal.index, y=dfinal["price"].where(strategy.order.values == "sell"), color="r", marker="x")
plt.scatter(x=dfinal.index, y=dfinal["price"].where(strategy.order.values == "buy"), color="g", marker="x")
# ax = strategy.plot(x="date", y=["price"], kind="scatter")
# ax = chart.plot(x="date", y=["close", "short_ema", "long_ema"], kind="line")
# plt.plot(ax=ax)

# f.plot(x="date", y=["close", "short_ema"], kind="line")
plt.show()

"""
# format the data to match the charting library
dates = []
open_data = []
high_data = []
low_data = []
close_data = []
for candle in candles:
    dates.append(datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f'))
    open_data.append(candle[1])
    high_data.append(candle[2])
    low_data.append(candle[3])
    close_data.append(candle[4])

# candlesticks chart
fig1 = go.Figure(data=[go.Candlestick(x=dates, open=open_data, high=high_data, low=low_data, close=close_data)])
fig1.show()

# line chart
fig2 = go.Figure(data=[go.Scatter(x=dates, y=close_data)])
fig2.show()
"""
