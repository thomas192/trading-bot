import time
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime

PAIR = 'BTC/USDT'
SHORT_SPAN = 10
LONG_SPAN = 20
STOP_LOSS = 3

# collect candlestick data from Binance
binance = ccxt.binance()
binance.load_markets()


def get_data(exchange, timef, from_datetime, to_datetime):
    msec = 1000
    minute = 60 * msec
    from_timestamp = exchange.parse8601(from_datetime)
    to_timestamp = exchange.parse8601(to_datetime)

    data = []

    while from_timestamp < to_timestamp:
        print(exchange.milliseconds(), 'Fetching candles starting from', exchange.iso8601(from_timestamp))
        ohlcvs = exchange.fetch_ohlcv(symbol=PAIR, timeframe=timef, since=from_timestamp)
        print(exchange.milliseconds(), 'Fetched', len(ohlcvs), 'candles')

        time.sleep(binance.rateLimit / msec)

        first = ohlcvs[0][0]
        last = ohlcvs[-1][0]
        print('First candle epoch', first, exchange.iso8601(first))
        print('Last candle epoch', last, exchange.iso8601(last))
        from_timestamp += len(ohlcvs) * 4 * 60 * minute

        data += ohlcvs

    return data


timeframe = "4h"
start_date = "2020-01-01 00:00:00"
end_date = "2020-01-02 00:00:00"
candles = get_data(binance, timeframe, start_date, end_date)
print("")

# format date
for candle in candles:
    candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

# create dataframe
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]

# calculate change
chart["change"] = (chart["close"] - chart["open"]) / chart["open"] * 100


def ema(df, name, n):
    price = df["close"]
    price.fillna(method='ffill', inplace=True)
    price.fillna(method='bfill', inplace=True)
    # ema = pd.Series(price.ewm(span=n, min_periods=n).mean(), name='EMA_{}'.format(n))
    # df = df.join(ema)
    df[name] = price.ewm(span=n, min_periods=n).mean()
    return df


# add indicators to dataframe
chart = ema(chart, "short_ema", SHORT_SPAN)
chart = ema(chart, "long_ema", LONG_SPAN)
# df['short_ema'] = df['close'].ewm(span=20, min_periods=20).mean()

# backtest
strategy = pd.DataFrame(chart["date"])
strategy["order"] = ""
strategy["price"] = np.nan
trades = pd.DataFrame(columns=["buy_price", "sell_price", "change"])
curr_trade_change = 0

positioned = False
capital_change = 0
trade_buy_price = np.nan
trade_sell_price = np.nan
for index, row in chart.iterrows():
    """if positioned:
        # track capital change
        capital_change += chart.at[index, "change"]"""

    if index != 0:
        # ema cross strategy
        if chart.at[index - 1, "short_ema"] > chart.at[index - 1, "long_ema"] and positioned is False:
            strategy.at[index, "order"] = "buy"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_buy_price = chart.at[index, "open"]
            positioned = True
        elif chart.at[index - 1, "short_ema"] < chart.at[index - 1, "long_ema"] and positioned is True:
            strategy.at[index, "order"] = "sell"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_sell_price = chart.at[index, "open"]
            positioned = False

    if not np.isnan(trade_buy_price) and not np.isnan(trade_sell_price):
        curr_trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
        row = pd.Series([trade_buy_price, trade_sell_price, curr_trade_change], index=["buy_price", "sell_price",
                                                                                       "change"])
        trades = trades.append(row, ignore_index=True)
        trade_buy_price = np.nan
        trade_sell_price = np.nan

    """if positioned and not np.isnan(trade_buy_price):
        # track trade change
        curr_trade_change += chart.at[index, "change"]
        # stop loss
        if curr_trade_change < -STOP_LOSS:
            strategy.at[index, "order"] = "sell"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_sell_price = chart.at[index, "open"]
            positioned = False

    if not positioned and not np.isnan(trade_sell_price):
        # track trade change
        curr_trade_change += chart.at[index, "change"]
        # save trade
        row = pd.Series([trade_buy_price, trade_sell_price, curr_trade_change], index=["buy_price", "sell_price",
                                                                                       "change"])
        trades = trades.append(row, ignore_index=True)
        # reset trade info at end of trade
        curr_trade_change = 0
        trade_buy_price = np.nan
        trade_sell_price = np.nan"""

# strategy performance
capital_change = round(trades["change"].sum(), 1)

nb_trades = len(trades)
winning_trades = trades[trades["change"] > 0]
losing_trades = trades[trades["change"] < 0]
nb_winning_trades = len(winning_trades)
nb_losing_trades = len(losing_trades)
avg_winning_trade = round(winning_trades["change"].mean(), 1)
avg_losing_trade = round(losing_trades["change"].mean(), 1)

avg_profit = round(trades["change"].mean(), 1)
max_loss = round(trades["change"].min(), 1)
# pair change
pair_change = round((chart.at[chart.index[-1], "close"] - chart.at[chart.index[0], "open"])
                    / chart.at[chart.index[0], "open"] * 100, 1)

# display results
print(PAIR + " change: " + str(pair_change) + " %")
print("capital change: " + str(capital_change) + " %")
print(str(nb_trades) + " trades: " + str(nb_losing_trades) + " losing " + str(nb_winning_trades)
      + " winning")
print("average profit: " + str(avg_profit) + " %")
print("average winning: " + str(avg_winning_trade) + " %")
print("average losing: " + str(avg_losing_trade) + " %")
print("maximum loss: " + str(max_loss) + " %")

# print(strategy.iloc[np.where(strategy.order.values == "sell")])
# print(strategy[strategy["order"] == "buy"].count())
# print(strategy[strategy["order"] == "sell"].count())
# df["buy"][df.short_ema > df.long_ema] = 1

# make plot
dfinal = pd.merge(chart, strategy, on="date", how="left")
plt.plot(dfinal["close"])
plt.plot(dfinal["short_ema"], color="y")
plt.plot(dfinal["long_ema"], color="m")
plt.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "sell"), color="r", marker="x")
plt.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "buy"), color="g", marker="x")
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
