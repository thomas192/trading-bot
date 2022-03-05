from Indicator import Indicator

# 15min bb_strategy variables
BB_WINDOW = 21
BB_STD = 2
VWMA_WINDOW = 21
RSI_WINDOW = 21
RSI_HIGH_BAND = 65
RSI_LOW_BAND = 30
"""# ETH
STOP_LOSS = -0.58
HIGHER_STOP_LOSS = -0.58"""
STOP_LOSS = -0.5
HIGHER_STOP_LOSS = -0.5


class Strategy:

    @staticmethod
    def bb_strategy_bt(df, index, positioned, hold, overbought, oversold, trade_buy_price, stop_loss):
        # Compute indicators needed
        if not df.__contains__("bb_avg"):
            Indicator.add_indicator(df=df, indicator_name="bb", window=BB_WINDOW, std=BB_STD)
        if not df.__contains__("vwma"):
            Indicator.add_indicator(df=df, indicator_name="vwma", col_name="vwma", window=VWMA_WINDOW)
        if not df.__contains__("rsi"):
            Indicator.add_indicator(df=df, indicator_name="rsi", col_name="rsi", window=RSI_WINDOW)

        prev_candle = index - 1
        if index != 0:
            # Determine if pair is overbought or oversold
            # IF RSI < LOW BAND
            if df.at[prev_candle, "rsi"] < RSI_LOW_BAND:
                oversold = True
            # ELIF RSI > HIGH BAND
            elif df.at[prev_candle, "rsi"] > RSI_HIGH_BAND:
                overbought = True
            # HIGH BAND > RSI > LOW BAND
            else:
                overbought = False
                oversold = False

            # Determine if current trade change exceeded stop loss
            if positioned is True:
                curr_trade_change = (df.at[prev_candle, "close"] - trade_buy_price) / trade_buy_price * 100
                if curr_trade_change < stop_loss:
                    # SELL
                    return "sell"

            # Determine if buy, sell or do nothing
            if hold is True:
                # IF NOT OVERBOUGHT ANYMORE
                if overbought is False:
                    # SELL
                    return "sell"

            # IF LOW < BB_LOW AND NOT OVERSOLD AND NOT POSITIONED
            if df.at[prev_candle, "low"] < df.at[prev_candle, "bb_low"] and oversold is False and positioned is False:
                # BUY
                return "buy"

            # IF CLOSE > BB_AVG AND POSITIONED
            if df.at[prev_candle, "close"] > df.at[prev_candle, "bb_avg"] and positioned is True:
                # IF CLOSE < VWMA
                if df.at[prev_candle, "close"] < df.at[prev_candle, "vwma"]:
                    # SELL
                    return "sell"
                # IF CLOSE > VWMA
                else:
                    # IF CLOSE > BB_UP
                    if df.at[prev_candle, "close"] > df.at[prev_candle, "bb_up"]:
                        # IF NOT OVERBOUGHT
                        if overbought is False:
                            # SELL
                            return "sell"
                        # IF OVERBOUGHT
                        else:
                            # HOLD LONGER
                            return "hold"
                    # CLOSE < BB_UP
                    else:
                        return "set_stop_loss"
            else:
                return False
        else:
            return False

    @staticmethod
    def bb_strategy(prev_candle, positioned, hold, overbought, oversold, trade_buy_price):
        # Determine if pair is overbought or oversold
        # IF RSI < LOW BAND
        if prev_candle["rsi"] < RSI_LOW_BAND:
            oversold = True
        # ELIF RSI > HIGH BAND
        elif prev_candle["rsi"] > RSI_HIGH_BAND:
            overbought = True
        # HIGH BAND > RSI > LOW BAND
        else:
            overbought = False
            oversold = False

        # Determine if current trade change exceeded stop loss
        if positioned is True:
            curr_trade_change = (prev_candle["close"] - trade_buy_price) / trade_buy_price * 100
            if curr_trade_change < STOP_LOSS:
                # SELL
                return "sell"

        # Determine if buy, sell or do nothing

        if hold:
            # IF NOT OVERBOUGHT ANYMORE
            if not overbought:
                # SELL
                return "sell"

        # IF LOW < BB_LOW AND NOT OVERSOLD AND NOT POSITIONED
        if prev_candle["low"] < prev_candle["bb_low"] and not oversold and not positioned:
            # BUY
            return "buy"

        # IF POSITIONED AND CLOSE > BB_AVG
        if positioned and prev_candle["close"] > prev_candle["bb_avg"]:
            # IF CLOSE < VWMA
            if prev_candle["close"] < prev_candle["vwma"]:
                # SELL
                return "sell"
            # IF CLOSE > VWMA
            else:
                # IF CLOSE > BB_UP
                if prev_candle["close"] > prev_candle["bb_up"]:
                    # IF NOT OVERBOUGHT
                    if not overbought:
                        # SELL
                        return "sell"
                    # IF OVERBOUGHT
                    else:
                        # HOLD LONGER
                        return "hold"
