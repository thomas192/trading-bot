import numpy as np
import pandas as pd

from Binance import Binance
from Result import Result
from Strategy import Strategy, STOP_LOSS, HIGHER_STOP_LOSS

# ---- Gather data ---- #

# Data parameters
TIMEFRAME = "15m"
START_DATE = "2018-10-01 00:00:00"
END_DATE = "2018-12-01 00:01:00"
PAIR = 'ETH/USDT'

# Get data
binance = Binance()
candles = binance.get_data(PAIR, TIMEFRAME, START_DATE, END_DATE)
print("")

# ---- Backtest ---- #

# Create dataframe for OHLCV
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]

# Calculate change
chart["change"] = (chart["close"] - chart["open"]) / chart["open"] * 100

# Create dataframe for buy and sell prices
strategy = pd.DataFrame(chart["date"])
strategy["order"] = ""
strategy["price"] = np.nan

# Create dataframe for trades info
trades = pd.DataFrame(columns=["buy_price", "sell_price", "trade_change"])
trade_buy_price = np.nan
trade_sell_price = np.nan

# Strategy parameters
positioned = False
hold = False
overbought = False
oversold = False
stop_loss = STOP_LOSS

# Run simulation
for index, row in chart.iterrows():

    action = Strategy.bb_strategy(chart, index, positioned, hold, overbought, oversold, trade_buy_price, stop_loss)

    if action is not False:
        if action == "buy":
            # Buy
            strategy.at[index, "order"] = "buy"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_buy_price = chart.at[index, "open"]
            positioned = True
        elif action == "sell":
            # Sell
            strategy.at[index, "order"] = "sell"
            strategy.at[index, "price"] = chart.at[index, "open"]
            trade_sell_price = chart.at[index, "open"]
            positioned = False
            hold = False
            # Save trade
            trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
            row = pd.Series([trade_buy_price, trade_sell_price, trade_change], index=["buy_price", "sell_price",
                                                                                      "trade_change"])
            trades = trades.append(row, ignore_index=True)
            trade_buy_price = np.nan
            trade_sell_price = np.nan
            stop_loss = STOP_LOSS
        elif action == "set_stop_loss":
            # Set stop loss higher
            stop_loss = HIGHER_STOP_LOSS
        elif action == "hold":
            # Hold longer
            hold = True

# ---- Result ---- #

Result.strategy_performance(trades, chart, PAIR)

Result.strategy_plot(chart, strategy)
