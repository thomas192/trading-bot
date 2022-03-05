import time
import ccxt
from datetime import datetime


class Binance:

    def __init__(self):
        self.binance = ccxt.binance()
        self.binance.load_markets()

    def get_data(self, pair, timeframe, from_datetime, to_datetime):
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

        while from_timestamp < to_timestamp:
            print(self.binance.milliseconds(), 'Fetching candles starting from', self.binance.iso8601(from_timestamp))
            ohlcvs = self.binance.fetch_ohlcv(symbol=pair, timeframe=timeframe, since=from_timestamp)
            print(self.binance.milliseconds(), 'Fetched', len(ohlcvs), 'candles')

            time.sleep(self.binance.rateLimit / msec)

            first = ohlcvs[0][0]
            last = ohlcvs[-1][0]
            print('First candle epoch', first, self.binance.iso8601(first))
            print('Last candle epoch', last, self.binance.iso8601(last))
            from_timestamp += len(ohlcvs) * week * day * hour * minute

            candles += ohlcvs

        # format date
        for candle in candles:
            candle[0] = datetime.fromtimestamp(candle[0] / 1000.0).strftime('%Y-%m-%d %H:%M:%S.%f')

        return candles
