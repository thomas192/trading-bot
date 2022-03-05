import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD


def compute_sma(df, price, col_name, window):
    df[col_name] = price.rolling(window).mean()

    return df


def compute_ema(df, price, col_name, window):
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
    """
    delta = df["close"].diff().dropna()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    roll_up = up.rolling(window).mean()
    roll_down = down.abs().rolling(window).mean()
    rs = roll_up / roll_down
    df[col_name] = 100.0 - (100.0 / (1.0 + rs))
    """
    indicator_rsi = RSIIndicator(df["close"], window)
    df[col_name] = indicator_rsi.rsi()

    return df


def compute_atr(df, col_name, window):
    data = df.copy()
    high = data["high"]
    low = data["low"]
    close = data["close"]
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    df[col_name] = tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    return df


def compute_macd(df, col_name, n_fast, n_slow, n_signal):
    indicator_macd = MACD(df["close"], n_slow, n_fast, n_signal)
    df[str(col_name) + "_diff"] = indicator_macd.macd_diff()
    df[str(col_name) + "_signal"] = indicator_macd.macd_signal()

    return df


def compute_ichimoku_cloud(df):
    # Tenkan-sen (conversion line): (9-period high + 9-period low) / 2
    nine_period_high = df["high"].rolling(window=9).max()
    nine_period_low = df["low"].rolling(window=9).min()
    df["tenkansen"] = (nine_period_high + nine_period_low) / 2

    # Kijun-sen (base line): (26-period high + 26-period low) / 2
    period26_high = df["high"].rolling(window=26).max()
    period26_low = df["low"].rolling(window=26).min()
    df["kijunsen"] = (period26_high + period26_low) / 2

    # Senkou span A (leading span A): conversion line + base line) / 2
    df["senkou_a"] = ((df["tenkansen"] + df["kijunsen"]) / 2).shift(26)

    # Senkou span B
    period52_high = df["high"].rolling(window=52).max()
    period52_low = df["low"].rolling(window=52).min()
    df["senkou_b"] = ((period52_high + period52_low) / 2).shift(52)

    # Chikou span: the most recent closing price, plotted 26 periods behind
    df["chikou_span"] = df["close"].shift(-26)

    return df


class Indicator:
    INDICATORS_DICT = {
        "sma": compute_sma,
        "ema": compute_ema,
        "bb": compute_bollinger_bands,
        "vwma": compute_vwma,
        "rsi": compute_rsi,
        "atr": compute_atr,
        "macd": compute_macd,
    }

    @staticmethod
    def add_indicator(df, indicator_name, price=False, col_name=False, window=False, std=False):
        try:
            if indicator_name == "sma":
                df = compute_sma(df, price, col_name, window)
            elif indicator_name == "ema":
                df = compute_ema(df, price, col_name, window)
            elif indicator_name == "bb":
                df = compute_bollinger_bands(df, window, std)
            elif indicator_name == "vwma":
                df = compute_vwma(df, col_name, window)
            elif indicator_name == "rsi":
                df = compute_rsi(df, col_name, window)
            elif indicator_name == "atr":
                df = compute_atr(df, col_name, window)
            elif indicator_name == "ichimoku_cloud":
                df = compute_ichimoku_cloud(df)

        except Exception as e:
            print("\nException raised when trying to compute " + indicator_name)
            print(e)
