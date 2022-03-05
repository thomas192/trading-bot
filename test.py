import time
import pandas as pd
from Binance import Binance
import logging

# logging.basicConfig(level=logging.DEBUG)

PAIR = "ETH/USDT"
TIMEFRAME = "1m"

# Get data
binance = Binance()
candles = binance.get_latest_data(PAIR, TIMEFRAME, 25)
# chart = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
# chart = candles
chart = pd.DataFrame(candles)
chart.columns = ["date", "open", "high", "low", "close", "volume"]
current_candle = chart.iloc[chart.index[-1]]
latest_complete_candle = chart.iloc[chart.index[-2]]
print(" Current candle : " + str(current_candle["date"]))
print(" Latest complete candle : " + str(latest_complete_candle["date"]))

# limits = binance.binance.markets["BTC/USDT"]["limits"]
# print(limits)

# order = binance.create_market_quote_order(PAIR, "buy", 500)
# order = binance.create_market_order(PAIR, "buy", 0.5)

print("\nETH : " + str(binance.get_balance("ETH")))

# Open orders
nb = binance.get_number_of_open_orders(PAIR)
print("\nNumber of open order : " + str(nb))

order_id = binance.get_id_of_latest_open_order(PAIR)
print(order_id)

# Stop loss order
"""limit_price = current_candle["open"] - current_candle["open"] * 0.065
stop_price = limit_price + 3
order_id = binance.create_stop_loss_order(PAIR, 0.01, round(stop_price, 1), round(limit_price, 1))
print("\nCreated order " + str(order_id))"""

# Limit order
"""limit_price = current_candle["open"] + 3
order = binance.binance.create_order(PAIR, "limit", "buy", amount=None, price=2400,
params={"quoteOrderQty": binance.binance.cost_to_precision(PAIR, 1000.1)})
order_id = order["id"]
order_id = binance.create_limit_quote_order(PAIR, "buy", round(limit_price, 1), 500)
order_id = binance.create_market_quote_order(PAIR, "buy", 500)
print("\nCreated order " + str(order_id))"""

# Check order status
"""status = binance.get_order_status(PAIR, order_id)
print("\n" + str(order_id) + " : " + str(status))"""

# print("\nUSDT : " + str(binance.get_balance("USDT")))

# Open orders
"""nb = binance.get_number_open_orders(PAIR)
print("\nNumber of open order : " + str(nb))"""

# Cancel order
# order_id = binance.cancel_order(PAIR, order_id)

# Check order status
"""status = binance.get_order_status(PAIR, order_id)
print("\n" + str(order_id) + " : " + str(status))"""

# Get id of latest open order
"""order_id = binance.get_id_of_latest_open_order(PAIR)
print(order_id)"""

# Open orders
"""orders = binance.binance.fetch_open_orders(PAIR)
print("\nNumber of open order : " + str(len(orders)))"""

# print("\nBTC : " + str(binance.get_balance("BTC")))

# print("USDT : " + str(binance.get_balance("USDT")))
# print("BTC : " + str(binance.get_balance("BTC")))
