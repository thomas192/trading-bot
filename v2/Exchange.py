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
