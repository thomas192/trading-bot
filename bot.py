from datetime import datetime
import time

import numpy as np
import pandas as pd
from ccxt import NetworkError

from Binance import Binance
from Indicator import Indicator
from Strategy import Strategy, STOP_LOSS, BB_WINDOW, BB_STD, VWMA_WINDOW, RSI_WINDOW

PAIR = "ETH/USDT"
ETH = "ETH"
USDT = "USDT"
TIMEFRAME = "5m"

# Get latest data
binance = Binance()
candles = binance.get_latest_data(PAIR, TIMEFRAME, 25)
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]
curr_candle = chart.iloc[chart.index[-1]]
prev_candle = chart.iloc[chart.index[-2]]
print("Current candle : " + str(curr_candle["date"]))
print("Previous candle : " + str(prev_candle["date"]))

# Create dataframe for trades info
trades = pd.DataFrame(columns=["date", "side", "price", "trade_change"])

# Strategy parameters
positioned = False
hold = False
overbought = False
oversold = False
trade_buy_price = np.nan
trade_sell_price = np.nan
stop_loss_id = None

while 1:
    try:
        # Get latest data
        candles = binance.get_latest_data(PAIR, TIMEFRAME, 25)
        chart = pd.DataFrame(candles)
        chart.columns = ["date", "open", "high", "low", "close", "volume"]

        # IF NEW CANDLE
        if curr_candle["date"] != chart.at[chart.index[-1], "date"]:
            # Update indicators
            if not chart.__contains__("bb_avg"):
                Indicator.add_indicator(df=chart, indicator_name="bb", window=BB_WINDOW, std=BB_STD)
            if not chart.__contains__("vwma"):
                Indicator.add_indicator(df=chart, indicator_name="vwma", col_name="vwma", window=VWMA_WINDOW)
            if not chart.__contains__("rsi"):
                Indicator.add_indicator(df=chart, indicator_name="rsi", col_name="rsi", window=RSI_WINDOW)
            # Update current candle and previous candle
            curr_candle = chart.iloc[chart.index[-1]]
            prev_candle = chart.iloc[chart.index[-2]]

            # IF STOP LOSS WAS TRIGGERED
            if not pd.isnull(stop_loss_id) and binance.get_status_of_order(PAIR, stop_loss_id) == "closed":
                positioned = False
                hold = False
                print("\nStop loss " + str(stop_loss_id) + " was triggered last candle")
                # Save trade
                trade_sell_price = binance.get_average_price_of_order(PAIR, stop_loss_id)
                trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
                row = pd.Series([curr_candle["date"], "sell", trade_sell_price, trade_change],
                                index=["date", "side", "price", "trade_change"])
                trades = trades.append(row, ignore_index=True)
                trade_buy_price = np.nan
                trade_sell_price = np.nan
                stop_loss_id = None
            else:
                # Get action
                action = Strategy.bb_strategy(prev_candle, positioned, hold, overbought, oversold, trade_buy_price)
                print("\n" + str(prev_candle["date"]) + " action: " + str(action))
                # Act
                if action is not False:
                    if action == "buy":
                        # Create buy market order
                        # amount = binance.get_balance(USDT)
                        amount = 15
                        order_id = binance.create_market_quote_order(PAIR, "buy", amount)
                        print("\nCreated BUY order " + str(order_id))
                        # WAIT FOR ORDER TO BE FILLED
                        while binance.get_status_of_order(PAIR, order_id) == "open":
                            print("\nWaiting for BUY order " + str(order_id) + " to be filled...")
                            time.sleep(0.3)
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
                            amount = binance.get_balance(ETH)
                            limit_price = trade_buy_price + trade_buy_price * STOP_LOSS / 100
                            stop_price = limit_price + 0.25
                            stop_loss_id = binance.create_stop_loss_order(PAIR, amount, stop_price, limit_price)
                            print("\nStop loss " + str(stop_loss_id) + " status: "
                                  + str(binance.get_status_of_order(PAIR, stop_loss_id)))
                            # Save trade
                            row = pd.Series([curr_candle["date"], "buy", trade_buy_price, np.nan],
                                            index=["date", "side", "price", "trade_change"])
                            trades = trades.append(row, ignore_index=True)

                    elif action == "sell":
                        # Cancel stop loss order
                        stop_loss_id = binance.cancel_order(PAIR, stop_loss_id)
                        # WAIT FOR STOP LOSS TO BE CANCELED
                        while binance.get_status_of_order(PAIR, stop_loss_id) == "open":
                            print("\nStop loss " + str(stop_loss_id + " not canceled..."))
                            time.sleep(0.3)
                        # IF ORDER CLOSED
                        if binance.get_status_of_order(PAIR, stop_loss_id) == "closed":
                            print("\nStop loss " + str(stop_loss_id) + " filled")
                        # ELIF ORDER CANCELED
                        elif binance.get_status_of_order(PAIR, stop_loss_id) == "canceled":
                            print("\nStop loss " + str(stop_loss_id) + " successfully canceled")
                            stop_loss_id = None
                        # Create sell market order
                        amount = binance.get_balance(ETH)
                        order_id = binance.create_market_order(PAIR, "sell", amount)
                        print("\nCreated SELL order " + str(order_id))
                        # WAIT FOR ORDER TO BE FILLED
                        while binance.get_status_of_order(PAIR, order_id) == "open":
                            print("\nWaiting for SELL order " + str(order_id) + " to be filled...")
                            time.sleep(0.3)
                        # IF ORDER CANCELED
                        if binance.get_status_of_order(PAIR, order_id) == "canceled":
                            print("\nSELL order " + str(order_id) + " canceled")
                        # ELIF ORDER CLOSED
                        elif binance.get_status_of_order(PAIR, order_id) == "closed":
                            positioned = False
                            hold = False
                            print("\nSELL order " + str(order_id) + " closed")
                            # Save trade
                            trade_sell_price = binance.get_average_price_of_order(PAIR, order_id)
                            trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100
                            row = pd.Series([curr_candle["date"], "sell", trade_sell_price, trade_change],
                                            index=["date", "side", "price", "trade_change"])
                            trades = trades.append(row, ignore_index=True)
                            trade_buy_price = np.nan
                            trade_sell_price = np.nan

                    elif action == "hold":
                        # Hold longer
                        print("\nHolding current position longer")
                        hold = True

            print("\n" + str(curr_candle["date"]) + " open at " + str(curr_candle["open"]) + "$")
            if positioned and not trades.empty:
                print("Currently positioned")
                trade_entry = trades.iloc[trades.index[-1]]
                print("Bought at " + str(round(trade_entry["price"], 2)) + "$ the " + str(trade_entry["date"]))
            elif not trades.empty:
                print("Currently not positioned")
                trade_exit = trades.iloc[trades.index[-1]]
                print("Latest trade: " + str(trade_exit))

        time.sleep(0.3)

    except NetworkError:
        print(str(datetime.now()) + " CONNECTION LOST...")
        continue
    except Exception as e:
        raise e
