from datetime import datetime
import time
import traceback

import numpy as np
import pandas as pd

from Firestore import Firestore
from Binance import Binance
from Indicator import Indicator
from Strategy import Strategy, STOP_LOSS, BB_WINDOW, BB_STD, VWMA_WINDOW, RSI_WINDOW

# ---- BOT SET UP ---- #

PAIR = "ETH/USDT"
ETH = "ETH"
USDT = "USDT"
TIMEFRAME = "15m"

# Create Firestore instance
firestore = Firestore()

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
trades = pd.DataFrame(columns=["date", "side", "price", "trade_change", "capital"])

# Bot variables
positioned = False
hold = False
overbought = False
oversold = False
trade_buy_price = np.nan
trade_sell_price = np.nan
stop_loss_id = None
order_id = None
save_point = None  # Used for handling errors
error = False  # Set to True each time an error occurs
nb_of_trades = len(trades)  # Used to know when to save trades in Firestore
trade_id = 0  # Increment after each trade insert
error_id = 0  # Increment after each error insert
traceback_str = ""  # Used to store the traceback
error_str = ""  # Used to store the error code

# ---- BOT LOOP ---- #

# IF LAUNCHING BOT WHILE CURRENTLY POSITIONED
if binance.get_number_of_open_orders(PAIR) > 0:
    print("\nLaunching bot while currently positioned...")
    buy_order_id = binance.get_id_of_latest_closed_order(PAIR)
    # Set parameters
    positioned = True
    trade_buy_price = binance.get_average_price_of_order(PAIR, buy_order_id)
    stop_loss_id = binance.get_id_of_latest_open_order(PAIR)
    print("trade_buy_price: " + str(trade_buy_price))
    print("stop_loss_id: " + str(stop_loss_id))

while 1:
    try:
        # IF AN ERROR OCCURRED DURING LAST ITERATION
        if error:
            # IF IT WAS DURING BUY ACTION
            if save_point == "buy":
                print("\nResolving error during last buy action...")
                # IF BUY ORDER WAS NOT CREATED
                if pd.isnull(order_id):
                    print("\nBuy order was not created")
                    # Create buy market order
                    amount = binance.get_balance(USDT)
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
                        print("\nBUY order " + str(order_id) + " closed")
                # If STOP LOSS ORDER WAS NOT CREATED
                if pd.isnull(stop_loss_id):
                    print("\nStop loss was not set")
                    # Get average filling price of market order
                    trade_buy_price = binance.get_average_price_of_order(PAIR, order_id)
                    # Set stop loss
                    amount = binance.get_balance(ETH)
                    limit_price = trade_buy_price + trade_buy_price * STOP_LOSS / 100
                    stop_price = limit_price + 0.25
                    stop_loss_id = binance.create_stop_loss_order(PAIR, amount, stop_price, limit_price)
                    print("\nStop loss " + str(stop_loss_id) + " created")
                    # Save trade
                    row = pd.Series([curr_candle["date"], "buy", trade_buy_price, np.nan, np.nan],
                                    index=["date", "side", "price", "trade_change", "capital"])
                    trades = trades.append(row, ignore_index=True)
                    #
                    order_id = None
                    save_point = None

            # IF IT WAS DURING SELL ACTION
            elif save_point == "sell":
                print("\nResolving error during last sell action...")
                # If STOP LOSS WAS NOT CANCELED
                if not pd.isnull(stop_loss_id):
                    print("\nStop loss was not canceled")
                    # Cancel stop loss order
                    stop_loss_id = binance.cancel_order(PAIR, stop_loss_id)
                    print("\n Created cancel order on stop loss: " + str(stop_loss_id))
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
                # IF SELL ORDER WAS NOT CREATED
                if pd.isnull(order_id):
                    print("\nSell order was not created")
                    print()
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
                        positioned = True
                        print("\nSELL order " + str(order_id) + " canceled")
                    # ELIF ORDER CLOSED
                    elif binance.get_status_of_order(PAIR, order_id) == "closed":
                        hold = False
                        print("\nSELL order " + str(order_id) + " closed")
                        # Save trade
                        trade_sell_price = binance.get_average_price_of_order(PAIR, order_id)
                        capital = binance.get_balance(USDT)
                        trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100 - 2 * 0.075
                        row = pd.Series([curr_candle["date"], "sell", trade_sell_price, trade_change, capital],
                                        index=["date", "side", "price", "trade_change", "capital"])
                        trades = trades.append(row, ignore_index=True)
                        trade_buy_price = np.nan
                        trade_sell_price = np.nan
                        #
                        order_id = None
                        save_point = None

            error = False
            print("\nError resolved or ignored if it did not occur during buy or sell action")
            # Save error in Firestore
            state_after_error = "positioned: " + str(positioned) + "\nhold: " + str(hold) \
                                + "\ntrade_buy_price: " + str(trade_buy_price) \
                                + "\ntrade_sell_price: " + str(trade_sell_price) \
                                + "\nstop_loss_id: " + str(stop_loss_id) \
                                + "\norder_id: " + str(order_id) \
                                + "\nsave_point: " + str(save_point) \
                                + "\nerror: " + str(error)
            firestore.save_error(error_id, datetime.now(), error_str, traceback_str, state_after_error)
            print("Error saved in Firestore")
            error_id = error_id + 1

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
                capital = binance.get_balance(USDT)
                trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100 - 2 * 0.075
                row = pd.Series([curr_candle["date"], "sell", trade_sell_price, trade_change, capital],
                                index=["date", "side", "price", "trade_change", "capital"])
                trades = trades.append(row, ignore_index=True)
                trade_buy_price = np.nan
                trade_sell_price = np.nan
                stop_loss_id = None

            else:
                # Get action
                action = Strategy.bb_strategy(prev_candle, positioned, hold, overbought, oversold, trade_buy_price)
                print("\n" + str(prev_candle["date"]) + " action: " + str(action))
                # Act
                if not pd.isnull(action):
                    if action == "buy":
                        save_point = "buy"
                        positioned = True
                        # Create buy market order
                        amount = binance.get_balance(USDT)
                        order_id = binance.create_market_quote_order(PAIR, "buy", amount)
                        print("\nCreated BUY order " + str(order_id))
                        # WAIT FOR ORDER TO BE FILLED
                        while binance.get_status_of_order(PAIR, order_id) == "open":
                            print("\nWaiting for BUY order " + str(order_id) + " to be filled...")
                            time.sleep(0.3)
                        # IF ORDER CANCELED
                        if binance.get_status_of_order(PAIR, order_id) == "canceled":
                            positioned = False
                            print("\nBUY order " + str(order_id) + " canceled")
                        # ELIF ORDER CLOSED
                        elif binance.get_status_of_order(PAIR, order_id) == "closed":
                            print("\nBUY order " + str(order_id) + " closed")
                            # Get average filling price of market order
                            trade_buy_price = binance.get_average_price_of_order(PAIR, order_id)
                            # Set stop loss
                            amount = binance.get_balance(ETH)
                            limit_price = trade_buy_price + trade_buy_price * STOP_LOSS / 100
                            stop_price = limit_price + 0.15
                            stop_loss_id = binance.create_stop_loss_order(PAIR, amount, stop_price, limit_price)
                            print("\nStop loss " + str(stop_loss_id) + " created")
                            # Save trade
                            row = pd.Series([curr_candle["date"], "buy", trade_buy_price, np.nan, np.nan],
                                            index=["date", "side", "price", "trade_change", "capital"])
                            trades = trades.append(row, ignore_index=True)
                            #
                            order_id = None
                            save_point = None

                    elif action == "sell":
                        save_point = "sell"
                        positioned = False
                        # Cancel stop loss order
                        stop_loss_id = binance.cancel_order(PAIR, stop_loss_id)
                        print("\n Created cancel order on stop loss: " + str(stop_loss_id))
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
                            positioned = True
                            print("\nSELL order " + str(order_id) + " canceled")
                        # ELIF ORDER CLOSED
                        elif binance.get_status_of_order(PAIR, order_id) == "closed":
                            hold = False
                            print("\nSELL order " + str(order_id) + " closed")
                            # Save trade
                            trade_sell_price = binance.get_average_price_of_order(PAIR, order_id)
                            capital = binance.get_balance(USDT)
                            trade_change = (trade_sell_price - trade_buy_price) / trade_buy_price * 100 - 2 * 0.075
                            row = pd.Series([curr_candle["date"], "sell", trade_sell_price, trade_change, capital],
                                            index=["date", "side", "price", "trade_change", "capital"])
                            trades = trades.append(row, ignore_index=True)
                            trade_buy_price = np.nan
                            trade_sell_price = np.nan
                            #
                            order_id = None
                            save_point = None

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

        # IF A TRADE WAS MADE
        if nb_of_trades != len(trades):
            nb_of_trades = len(trades)
            row = trades.iloc[trades.index[-1]]
            firestore.save_trade(trade_id, PAIR, row)
            trade_id = trade_id + 1

        time.sleep(0.6)

    except Exception as e:
        error = True
        traceback.print_exc()
        traceback_str = traceback.format_exc()
        error_str = e
        time.sleep(0.3)
        continue
