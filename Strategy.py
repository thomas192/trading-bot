from Indicator import Indicator

# Parameters for bb_strategy
BB_WINDOW = 20
BB_STD = 2
VWMA_WINDOW = 20
RSI_WINDOW = 21
RSI_HIGH_BAND = 65
RSI_LOW_BAND = 30
STOP_LOSS = 0.6


class Strategy:

    @staticmethod
    def bb_strategy(df, index, positioned, hold, trade_buy_price):
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
                if curr_trade_change < -STOP_LOSS:
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
            else:
                return False
        else:
            return False
