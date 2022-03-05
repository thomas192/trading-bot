import numpy as np
import pandas as pd

from Binance import Binance
from Result import Result
from Strategy import STOP_LOSS, HIGHER_STOP_LOSS, Strategy

# ---- DATA SET UP ---- #

TIMEFRAME = "15m"
START_DATE = "2020-11-20 00:00:00"
END_DATE = "2020-11-24 00:01:00"
PAIRS = ["ETH/USDT"]
"""PAIRS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "DOT/USDT", "ATOM/USDT", "VET/USDT", "AAVE/USDT", "SNX/USDT", "ADA/USDT"
            ,"XMR/USDT", "LINK/USDT", "EOS/USDT", "LTC/USDT", "MKR/USDT", "XRP/USDT"]"""
CAPITAL = 2000
SAVE_PATH = "Research/bb_strategy/"

binance = Binance()
for pair in PAIRS:
    # Get data
    candles = binance.get_data(pair, TIMEFRAME, START_DATE, END_DATE)
    # candles = binance.get_latest_data(PAIR, TIMEFRAME, 100)
    print("")

    # ---- SIMULATION SET UP ---- #

    # Create dataframe for OHLCV
    chart = pd.DataFrame(candles)
    chart.columns = ["date", "open", "high", "low", "close", "volume"]

    # Calculate change
    chart["change"] = (chart["close"] - chart["open"]) / chart["open"] * 100

    # Create dataframe for trades info
    trades = pd.DataFrame(columns=["date", "side", "price", "trade_change", "capital"])

    # Parameters
    positioned = False
    hold = False
    overbought = False
    oversold = False
    losses_counter = 0
    trade_buy_price = np.nan
    trade_sell_price = np.nan
    stop_loss = STOP_LOSS
    capital = CAPITAL

    # ---- RUN SIMULATION ---- #

    for index, row in chart.iterrows():
        # IF POSITIONED
        if positioned:
            # Calculate change between trade_buy_price and last candle low
            chg = (chart.at[index - 1, "low"] - trade_buy_price) / trade_buy_price * 100
            # IF PREVIOUS CANDLE LOW TRIGGERED STOP LOSS
            if chg < stop_loss:
                positioned = False
                hold = False
                losses_counter += 1
                # Save trade
                trade_change = stop_loss
                trade_change = trade_change - 2 * 0.075
                trade_sell_price = trade_buy_price + trade_buy_price * stop_loss / 100
                capital = capital + capital * trade_change / 100
                row = pd.Series([chart.at[index - 1, "date"], "sell", trade_sell_price, trade_change, capital],
                                index=["date", "side", "price", "trade_change", "capital"])
                trades = trades.append(row, ignore_index=True)
                stop_loss_price = np.nan
                trade_buy_price = np.nan
                trade_sell_price = np.nan
                #
                # action = False

        """action = Strategy.bb_strategy_bt(chart, index, positioned, hold, overbought, oversold, losses_counter,
                                         trade_buy_price, stop_loss)"""

        action = Strategy.ichimoku_cloud_strategy_bt(chart, index, positioned, hold, trade_buy_price, stop_loss)

        if action is not False:
            if action == "buy":
                # Buy
                positioned = True
                trade_buy_price = chart.at[index, "open"]
                # Save trade
                trade_buy_date = chart.at[index, "date"]
                row = pd.Series([chart.at[index, "date"], "buy", trade_buy_price, np.nan],
                                index=["date", "side", "price", "trade_change"])
                trades = trades.append(row, ignore_index=True)

            elif action == "sell":
                # Sell
                positioned = False
                hold = False
                losses_counter = 0
                trade_sell_price = chart.at[index, "open"]
                # Save trade
                trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
                if trade_change < stop_loss:
                    trade_change = stop_loss
                trade_change = trade_change - 2 * 0.075
                capital = capital + capital * trade_change / 100
                row = pd.Series([chart.at[index, "date"], "sell", trade_sell_price, trade_change, capital],
                                index=["date", "side", "price", "trade_change", "capital"])
                trades = trades.append(row, ignore_index=True)
                trade_buy_price = np.nan
                trade_sell_price = np.nan
                # stop_loss = STOP_LOSS

            elif action == "reset_loss_counter":
                losses_counter = 0

            elif action == "set_stop_loss":
                # Set stop loss higher
                stop_loss = HIGHER_STOP_LOSS

            elif action == "hold":
                # Hold longer
                hold = True

    # ---- RESULT ---- #

    print(chart.iloc[400])

    Result.strategy_performance(pair, TIMEFRAME, trades, chart, SAVE_PATH)
