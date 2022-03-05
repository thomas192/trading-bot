import numpy as np


def compute_sma(df, col_name, window):
    rolling_mean = df["close"].rolling(window).mean()
    df[col_name] = rolling_mean

    return df


def compute_ema(df, col_name, window):
    price = df["close"]
    price.fillna(method='ffill', inplace=True)
    price.fillna(method='bfill', inplace=True)
    df[col_name] = price.ewm(span=window, min_periods=window).mean()

    return df


def compute_bollinger_bands(df, window, std):
    roll_mean = df["close"].rolling(window).mean()
    roll_std = df["close"].rolling(window).std(ddof=0)
    df["bb_avg"] = roll_mean
    df["bb_low"] = roll_mean - (roll_std * std)
    df["bb_up"] = roll_mean + (roll_std * std)

    return df


def compute_vwma(df, col_name, window):
    df[col_name] = np.nan
    window -= 1
    timeframe = df["date"]
    for index, value in timeframe.iteritems():
        if index >= window:
            temp = df.loc[index - window:index]
            df.at[index, col_name] = ((temp["high"] + temp["low"] + temp["close"]) / 3 * temp["volume"]).sum() / temp[
                "volume"].sum()

    return df


def compute_rsi(df, col_name, window):
    delta = df["close"].diff().dropna()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    roll_up = up.rolling(window).mean()
    roll_down = down.abs().rolling(window).mean()
    rs = roll_up / roll_down
    df[col_name] = 100.0 - (100.0 / (1.0 + rs))

    return df


class Indicator:
    INDICATORS_DICT = {
        "sma": compute_sma,
        "ema": compute_ema,
        "bb": compute_bollinger_bands,
        "vwma": compute_vwma,
        "rsi": compute_rsi
    }

    @staticmethod
    def add_indicator(df, indicator_name, col_name=False, window=False, std=False):
        try:
            if indicator_name == "sma":
                df = compute_sma(df, col_name, window)
            elif indicator_name == "ema":
                df = compute_ema(df, col_name, window)
            elif indicator_name == "bb":
                df = compute_bollinger_bands(df, window, std)
            elif indicator_name == "vwma":
                df = compute_vwma(df, col_name, window)
            elif indicator_name == "rsi":
                df = compute_rsi(df, col_name, window)
        except Exception as e:
            print("\nException raised when trying to compute " + indicator_name)
            print(e)
