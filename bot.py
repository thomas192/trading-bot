import time
import numpy as np
import pandas as pd

from Indicator import Indicator
from Binance import Binance
from Strategy import Strategy, STOP_LOSS, HIGHER_STOP_LOSS

PAIR = "BTC/USDT"
BTC = "BTC"
USDT = "USDT"
TIMEFRAME = "1m"

# Get latest data
binance = Binance()
candles = binance.get_latest_data(PAIR, TIMEFRAME, 25)
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]
curr_candle = chart.iloc[chart.index[-1]]
prev_candle = chart.iloc[chart.index[-2]]
print("Current candle : " + str(curr_candle["date"]))
print("Latest complete candle : " + str(prev_candle["date"]))

# Create dataframe for trades info
trades = pd.DataFrame(columns=["date", "side", "price", "trade_change"])

trade_buy_price = np.nan
trade_sell_price = np.nan

# Strategy parameters
positioned = False
hold = False
overbought = False
oversold = False
stop_loss = STOP_LOSS
stop_loss_id = np.nan

while 1:
    """try:"""
    # Get latest data
    candles = binance.get_latest_data(PAIR, TIMEFRAME, 25)
    chart = pd.DataFrame(candles)
    chart.columns = ["date", "open", "high", "low", "close", "volume"]

    # IF NEW CANDLE
    if curr_candle["date"] != chart.at[chart.index[-1], "date"]:
        # Update current candle and previous candle
        curr_candle = chart.iloc[chart.index[-1]]
        prev_candle = chart.iloc[chart.index[-2]]
        # Get action
        action = Strategy.bb_strategy(chart, prev_candle, positioned, hold, overbought, oversold, trade_buy_price)
        # Act
        if action is not False:
            if action == "buy":
                # Create buy market order
                # amount = binance.get_balance(USDT)
                amount = 10
                order_id = binance.create_market_quote_order(PAIR, "buy", amount)
                print("\nCreated BUY order " + str(order_id))
                # WAIT FOR ORDER TO BE FILLED
                while binance.get_status_of_order(PAIR, order_id) == "open":
                    print("\nWaiting for BUY order " + str(order_id) + " to be filled...")
                    time.sleep(0.4)
                else:
                    # IF ORDER CANCELED
                    if binance.get_status_of_order(PAIR, order_id) == "canceled":
                        print("\nBUY order " + str(order_id) + " canceled")
                    # ELIF ORDER CLOSED
                    elif binance.get_status_of_order(PAIR, order_id) == "closed":
                        positioned = True
                        print("\nBUY order " + str(order_id) + " closed")
                        # Get average filling price of market order
                        trade_buy_price = binance.get_average_price_of_order(PAIR, order_id)
                        # Set stop loss
                        amount = binance.get_balance(BTC)
                        limit_price = trade_buy_price - trade_buy_price * STOP_LOSS
                        stop_price = limit_price + 3
                        stop_loss_id = binance.create_stop_loss_order(PAIR, amount, stop_price, limit_price)
                        # Save trade
                        row = pd.Series([curr_candle["date"], "buy", trade_buy_price, np.nan],
                                        index=["date", "side", "price", "trade_change"])
                        trades = trades.append(row, ignore_index=True)

            elif action == "sell":
                # Create sell market order
                amount = binance.get_balance(BTC)
                order_id = binance.create_market_order(PAIR, "sell", amount)
                print("\nCreated SELL order " + str(order_id))
                # WAIT FOR ORDER TO BE FILLED
                while binance.get_status_of_order(PAIR, order_id) == "open":
                    print("\nWaiting for SELL order " + str(order_id) + " to be filled...")
                    time.sleep(0.4)
                else:
                    # IF ORDER CANCELED
                    if binance.get_status_of_order(PAIR, order_id) == "canceled":
                        print("\nSELL order " + str(order_id) + " canceled")
                    # ELIF ORDER CLOSED
                    elif binance.get_status_of_order(PAIR, order_id) == "closed":
                        positioned = False
                        hold = False
                        print("\nSELL order " + str(order_id) + " closed")
                        # Get average filling price of market order
                        trade_sell_price = binance.get_average_price_of_order(PAIR, order_id)
                        # Save trade
                        row = pd.Series([curr_candle["date"], "sell", trade_buy_price, trade_sell_price],
                                        index=["date", "side", "price", "trade_change"])
                        trades = trades.append(row, ignore_index=True)
                        trade_buy_price = np.nan
                        trade_sell_price = np.nan

            elif action == "hold":
                # Hold longer
                print("\nHolding current position longer")
                hold = True

        print("\n" + str(curr_candle["date"]) + " open : "+str(curr_candle["open"])+"$")
        if positioned and not trades.empty:
            print("Currently positioned")
            trade_entry = trades.iloc[trades.index[-1]]
            print("Bought at " + trade_entry["price"] + "$ the " + trade_entry["date"])
        elif not trades.empty:
            print("Currently not positioned")
            trade_exit = trades.iloc[trades.index[-1]]
            print("Latest trade change : " + str(trade_exit["trade_change"]))

    time.sleep(0.5)

    """except Exception as e:
        print("error")
        break"""
