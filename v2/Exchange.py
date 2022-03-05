import ccxt
import time
from datetime import datetime


class Exchange:

    def __init__(self, exchange, key, secret):

        if exchange == 'binance':
            self.exchange = ccxt.binance()
        elif exchange == 'ftx':
            self.exchange = ccxt.ftx()
        else:
            print('Error: exchange unknown')

        self.exchange.apiKey = key
        self.exchange.secret = secret
        self.exchange.enableRateLimit = True

        if self.exchange.check_required_credentials():
            self.exchange.load_markets()
        else:
            print('Error: credentials invalid')

    """Retrieves historical data for given date"""
    def get_data(self, symbol, timeframe, from_datetime, to_datetime):
        ms = 1000
        minute = 60 * ms
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

        from_timestamp = self.exchange.parse8601(from_datetime)
        to_timestamp = self.exchange.parse8601(to_datetime)

        data = []

        # Retrieve data
        while from_timestamp < to_timestamp:
            print(self.exchange.milliseconds(), 'Fetching candles starting from', self.exchange.iso8601(from_timestamp))
            ohlcvs = self.exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, since=from_timestamp)
            print(self.exchange.milliseconds(), 'Fetched', len(ohlcvs), 'candles')

            time.sleep(self.exchange.rateLimit / ms)

            first = ohlcvs[0][0]
            last = ohlcvs[-1][0]
            print('First candle epoch', first, self.exchange.iso8601(first))
            print('Last candle epoch', last, self.exchange.iso8601(last))
            from_timestamp = last
            data += ohlcvs

        # Format date
        for candle in data:
            candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

        return data
