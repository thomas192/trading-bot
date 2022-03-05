import matplotlib.pyplot as plt
import pandas as pd
from Strategy import STOP_LOSS, RSI_HIGH_BAND, RSI_LOW_BAND


class Result:

    @staticmethod
    def strategy_performance(df_trades, df_chart, pair):
        # Simulate real stop loss
        df_trades["trade_change"][df_trades["trade_change"] < STOP_LOSS] = STOP_LOSS

        # Simulate trading fees
        capital_change = df_trades["trade_change"].sum() - len(df_trades) * 2 * 0.075

        # Performance
        capital_change = round(capital_change, 2)
        nb_trades = len(df_trades)
        winning_trades = df_trades[df_trades["trade_change"] > 0]
        losing_trades = df_trades[df_trades["trade_change"] < 0]
        nb_winning_trades = len(winning_trades)
        nb_losing_trades = len(losing_trades)
        avg_winning_trade = round(winning_trades["trade_change"].mean(), 2)
        avg_losing_trade = round(losing_trades["trade_change"].mean(), 2)
        avg_profit = round(df_trades["trade_change"].mean(), 2)
        max_loss = round(df_trades["trade_change"].min(), 2)

        # Pair change
        pair_change = round((df_chart.at[df_chart.index[-1], "close"] - df_chart.at[df_chart.index[0], "open"])
                            / df_chart.at[df_chart.index[0], "open"] * 100, 2)

        # Display results
        print(pair + " change: " + str(pair_change) + " %")
        print("capital change: " + str(capital_change) + " %")
        print(str(nb_trades) + " trades: " + str(nb_losing_trades) + " losing " + str(nb_winning_trades)
              + " winning")
        print("average profit: " + str(avg_profit) + " %")
        print("average winning: " + str(avg_winning_trade) + " %")
        print("average losing: " + str(avg_losing_trade) + " %")
        print("maximum loss: " + str(max_loss) + " %")

    @staticmethod
    def strategy_plot(de_chart, df_strategy):
        # plotting
        dfinal = pd.merge(de_chart, df_strategy, on="date", how="left")
        fig, ax = plt.subplots()
        if dfinal.__contains__("close"):
            ax.plot(dfinal["close"])

        if dfinal.__contains__("rsi"):
            ax.plot(dfinal["close"].where(dfinal["rsi"] > RSI_HIGH_BAND), color="#17e336")
            ax.plot(dfinal["close"].where(dfinal["rsi"] < RSI_LOW_BAND), color="#e31717")

        if dfinal.__contains__("short_ema"):
            ax.plot(dfinal["short_ema"], color="#ffa600")

        if dfinal.__contains__("long_ema"):
            ax.plot(dfinal["long_ema"], color="#33ed09")

        if dfinal.__contains__("sma_50"):
            ax.plot(dfinal["sma_50"], color="#ffa600")

        if dfinal.__contains__("bb_avg"):
            ax.plot(dfinal["bb_avg"], color="#8332a8")
            ax.plot(dfinal["bb_low"], color="#8332a8")
            ax.plot(dfinal["bb_up"], color="#8332a8")

        if dfinal.__contains__("vwma"):
            ax.plot(dfinal["vwma"], color="#e3d517")

        if dfinal.__contains__("price"):
            ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "sell"), color="r", marker="x")
            ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["order"] == "buy"), color="g", marker="x")

        plt.show()
