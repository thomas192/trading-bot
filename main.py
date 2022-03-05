import time
import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from Strategy import Strategy

# data input
TIMEFRAME = "15m"
START_DATE = "2019-01-01 00:00:00"
END_DATE = "2019-01-01 00:01:00"
PAIR = 'ETH/USDT'

# strategy input
SHORT_SPAN = 10
LONG_SPAN = 20
BB_WINDOW = 20
BB_STD = 2
VWMA_WINDOW = 20
RSI_WINDOW = 21
RSI_HIGH_BAND = 65
RSI_LOW_BAND = 30
STOP_LOSS = 0.6

# collect candlestick data from Binance
binance = ccxt.binance()
binance.load_markets()


def get_data(exchange, timeframe, from_datetime, to_datetime):
    msec = 1000
    minute = 60 * msec
    hour = 1
    day = 1
    week = 1

    if timeframe == "1m":
        minute = 1 * minute
    elif timeframe == "3m":
        minute = 3 * minute
    elif timeframe == "5m":
        minute = 5 * minute
    elif timeframe == "15m":
        minute = 15 * minute
    elif timeframe == "30m":
        minute = 30 * minute
    elif timeframe == "1h":
        hour = 1 * 60
    elif timeframe == "2h":
        hour = 2 * 60
    elif timeframe == "4h":
        hour = 4 * 60
    elif timeframe == "8h":
        hour = 8 * 60
    elif timeframe == "1d":
        day = 1 * 24
    elif timeframe == "1w":
        week = 1 * 7

    from_timestamp = exchange.parse8601(from_datetime)
    to_timestamp = exchange.parse8601(to_datetime)

    data = []

    while from_timestamp < to_timestamp:
        print(exchange.milliseconds(), 'Fetching candles starting from', exchange.iso8601(from_timestamp))
        ohlcvs = exchange.fetch_ohlcv(symbol=PAIR, timeframe=timeframe, since=from_timestamp)
        print(exchange.milliseconds(), 'Fetched', len(ohlcvs), 'candles')

        time.sleep(binance.rateLimit / msec)

        first = ohlcvs[0][0]
        last = ohlcvs[-1][0]
        print('First candle epoch', first, exchange.iso8601(first))
        print('Last candle epoch', last, exchange.iso8601(last))
        from_timestamp += len(ohlcvs) * week * day * hour * minute

        data += ohlcvs

    return data


candles = get_data(binance, TIMEFRAME, START_DATE, END_DATE)
print("")

# format date
for candle in candles:
    candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

# create dataframe
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]

# calculate change
chart["change"] = (chart["close"] - chart["open"]) / chart["open"] * 100

# --- Backtesting --- #

# Plotting variables
strategy = pd.DataFrame(chart["date"])
strategy["order"] = ""
strategy["price"] = np.nan
trades = pd.DataFrame(columns=["buy_price", "sell_price", "change"])
trade_buy_price = np.nan
trade_sell_price = np.nan

# Strategy variables
positioned = False
hold = False

for index, row in chart.iterrows():

    action = Strategy.bb_strategy(chart, index, positioned, hold, trade_buy_price)

    if action is not False:
        if action == "buy":
            # BUY
            strategy.at[index, "order"] = "buy"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_buy_price = chart.at[index, "open"]
            positioned = True
        elif action == "sell":
            # SELL
            strategy.at[index, "order"] = "sell"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_sell_price = chart.at[index, "open"]
            positioned = False
            hold = False
            # SAVE TRADE
            trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
            row = pd.Series([trade_buy_price, trade_sell_price, trade_change], index=["buy_price", "sell_price",
                                                                                      "change"])
            trades = trades.append(row, ignore_index=True)
            trade_buy_price = np.nan
            trade_sell_price = np.nan
        elif action == "hold":
            hold = True

# simulate real stop loss
# trades["change"][trades["change"] < -STOP_LOSS] = -STOP_LOSS

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

# plotting
dfinal = pd.merge(chart, strategy, on="date", how="left")
fig, ax = plt.subplots()
if dfinal.__contains__("close"):
    ax.plot(dfinal["close"])

if dfinal.__contains__("rsi"):
    ax.plot(dfinal["close"].where(dfinal["rsi"] > RSI_HIGH_BAND), color="#17e336")
    ax.plot(dfinal["close"].where(dfinal["rsi"] < RSI_LOW_BAND), color="#e31717")

if dfinal.__contains__("short_ema"):
    ax.plot(dfinal["short_ema"], color="#ffa600")

if dfinal.__contains__("long_ema"):
    ax.plot(dfinal["long_ema"], color="#33ed09")

if dfinal.__contains__("sma_50"):
    ax.plot(dfinal["sma_50"], color="#ffa600")

if dfinal.__contains__("bb_avg"):
    ax.plot(dfinal["bb_avg"], color="#8332a8")
    ax.plot(dfinal["bb_low"], color="#8332a8")
    ax.plot(dfinal["bb_up"], color="#8332a8")

if dfinal.__contains__("vwma"):
    ax.plot(dfinal["vwma"], color="#e3d517")

if dfinal.__contains__("price"):
    ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "sell"), color="r", marker="x")
    ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "buy"), color="g", marker="x")

plt.show()
