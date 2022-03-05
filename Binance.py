import time
import ccxt
from datetime import datetime


class Binance:

    def __init__(self):
        self.binance = ccxt.binance()
        # Switch to testnet
        # self.binance.set_sandbox_mode(True)
        # Credentials
        self.binance.apiKey = 'AwBjO2ajlBUZCHpuFQbtXSfjLFJSmGuE0HwZij5ZfkyKNwf4KW3aJvi9pfiRdmTA'
        self.binance.secret = 'ij6jecXCAsMTL6OhVf8ttjCrH7A4KmKb2cbv9vGyeWvLxAODBIsvqbeH3csjMVRA'
        # Credentials for testnet
        # self.binance.apiKey = 'C0DsfrNhLDEVvWOvXXAKOD2GKioruMZoWn1zaVQ3YSJQ4bobdsYsERkdmxuKbpV2'
        # self.binance.secret = 'boOhj5889EjRS5Ctk99o1ERa37K9fioNGRqPum94QYbLSeabTHjkE98d3GUOOFX9'

        # Check if authentication was successful
        self.binance.check_required_credentials()

        self.binance.enableRateLimit = True
        self.binance.load_markets()

    def get_balance(self, currency):
        # Query
        balance = self.binance.fetch_balance()
        # Return funds available for trading
        return balance[currency]["free"]

    def get_status_of_order(self, symbol, order_id):
        # Query
        status = self.binance.fetch_order_status(order_id, symbol)
        # Return
        return status

    def get_average_price_of_order(self, symbol, order_id):
        # Query
        order = self.binance.fetch_order(order_id, symbol)
        # Return
        return order["average"]

    def get_id_of_latest_open_order(self, symbol):
        # Query
        orders = self.binance.fetch_open_orders(symbol)
        # Return
        return orders[-1]["id"]

    def get_number_of_open_orders(self, symbol):
        # Query
        orders = self.binance.fetch_open_orders(symbol)
        # Return
        return len(orders)

    def create_limit_quote_order(self, symbol, side, limit_price, quote_order_quantity):
        # Query
        order = self.binance.create_order(symbol, "limit", side, amount=None, price=limit_price,
                                          params={"quoteOrderQty": quote_order_quantity})
        # Results
        order_id = order["id"]
        # print("\nBinance order " + str(order_id) + " status : " + str(order["info"]["status"]))
        # print("CCXT order " + str(order_id) + " status : " + str(order["status"]))
        # Return
        return order_id

    def create_market_quote_order(self, symbol, side, quote_order_quantity):
        # Query
        order = self.binance.create_order(symbol, "market", side, amount=quote_order_quantity, price=None,
                                          params={"quoteOrderQty": quote_order_quantity})
        # Results
        order_id = order["id"]
        # print("\nBinance order " + str(order_id) + " status : " + str(order["info"]["status"]))
        # print("CCXT order " + str(order_id) + " status : " + str(order["status"]))
        # Return
        return order_id

    def create_market_order(self, symbol, side, amount):
        # Query
        order = self.binance.create_order(symbol, "market", side, amount, price=None)
        # Results
        order_id = order["id"]
        print("\nBinance order " + str(order_id) + " status : " + str(order["info"]["status"]))
        print("CCXT order " + str(order_id) + " status : " + str(order["status"]))
        # Return
        return order_id

    def create_stop_loss_order(self, symbol, amount, stop_price, limit_price):
        # Query
        order = self.binance.create_order(symbol, "stop_loss_limit", "sell", amount, limit_price,
                                          params={"stopPrice": stop_price})
        # Results
        order_id = order["id"]
        print("\nBinance order " + str(order_id) + " status : " + str(order["info"]["status"]))
        print("CCXT order " + str(order_id) + " status : " + str(order["status"]))
        # Return
        return order_id

    def cancel_order(self, symbol, order_id):
        # Query
        order = self.binance.cancel_order(order_id, symbol)
        # Return
        return order["id"]

    # Get the last n candles (max 500)
    def get_latest_data(self, symbol, timeframe, n):
        # Retrieve data
        candles = self.binance.fetch_ohlcv(symbol, timeframe, limit=n)
        # Format date
        for candle in candles:
            candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

        return candles

    def get_data(self, symbol, timeframe, from_datetime, to_datetime):
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

        from_timestamp = self.binance.parse8601(from_datetime)
        to_timestamp = self.binance.parse8601(to_datetime)

        candles = []

        # Retrieve data
        while from_timestamp < to_timestamp:
            print(self.binance.milliseconds(), 'Fetching candles starting from', self.binance.iso8601(from_timestamp))
            ohlcvs = self.binance.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=from_timestamp)
            print(self.binance.milliseconds(), 'Fetched', len(ohlcvs), 'candles')

            time.sleep(self.binance.rateLimit / msec)

            first = ohlcvs[0][0]
            last = ohlcvs[-1][0]
            print('First candle epoch', first, self.binance.iso8601(first))
            print('Last candle epoch', last, self.binance.iso8601(last))
            from_timestamp += len(ohlcvs) * week * day * hour * minute

            candles += ohlcvs

        # Format date
        for candle in candles:
            candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

        return candles
