import numpy as np
import pandas as pd


def sma(df, col_name, n):
    df[col_name] = df['close'].rolling(n).mean()


def atr(df, col_name, n):
    high_low = df['high'] - df['low']
    high_cp = np.abs(df['high'] - df['close'].shift())
    low_cp = np.abs(df['low'] - df['close'].shift())
    temp = pd.concat([high_low, high_cp, low_cp], axis=1)
    true_range = np.max(temp, axis=1)
    df[col_name] = true_range.rolling(n).mean()


def hfn(df, col_name, n):
    df[col_name] = np.nan
    timeframe = df['date']
    for i, val in timeframe.iteritems():
        if i >= n:
            temp = df.loc[i - n:i - 1]
            highs = temp['high']
            high = highs.max()
            df.at[i, col_name] = high


def lfn(df, col_name, n):
    df[col_name] = np.nan
    timeframe = df['date']
    for i, val in timeframe.iteritems():
        if i >= n:
            temp = df.loc[i - n:i - 1]
            lows = temp['low']
            low = lows.min()
            df.at[i, col_name] = low


class Indicator:

    @staticmethod
    def add_indicator(df, indicator_name, col_name, n):
        try:
            if indicator_name == 'hfn':
                hfn(df, col_name, n)
            elif indicator_name == 'lfn':
                lfn(df, col_name, n)
            elif indicator_name == 'atr':
                atr(df, col_name, n)
            elif indicator_name == 'sma':
                sma(df, col_name, n)

        except Exception as e:
            print("\nException raised when trying to compute " + indicator_name)
            print(e)
