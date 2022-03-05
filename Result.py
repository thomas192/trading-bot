import matplotlib.pyplot as plt
import pandas as pd

from Strategy import STOP_LOSS, RSI_HIGH_BAND, RSI_LOW_BAND


class Result:

    @staticmethod
    def strategy_performance(pair, timeframe, df_trades, df_chart, save_path):
        # Simulate trading fees
        nb_trades = len(df_trades[df_trades["trade_change"].notnull()])
        capital_change = df_trades["trade_change"].sum()

        # General performance
        capital_change = round(capital_change, 2)
        winning_trades = df_trades[df_trades["trade_change"] > 0]
        losing_trades = df_trades[df_trades["trade_change"] < 0]
        nb_winning_trades = len(winning_trades)
        nb_losing_trades = len(losing_trades)
        if nb_losing_trades > 0:
            win_loss_ratio = round(nb_winning_trades / nb_losing_trades, 2)
        else:
            win_loss_ratio = nb_winning_trades / 1
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
        print("win/loss ration: " + str(win_loss_ratio))
        print("average profit: " + str(avg_profit) + " %")
        print("average winning: " + str(avg_winning_trade) + " %")
        print("average losing: " + str(avg_losing_trade) + " %")
        print("maximum loss: " + str(max_loss) + " %")

        dfinal = pd.merge(df_chart, df_trades, on="date", how="right")
        fig, ax = plt.subplots()

        if dfinal.__contains__("close"):
            ax.plot(dfinal["close"])
            ax.set_ylabel("Price")
            ax.set_xlabel("From " + str(df_chart.at[df_chart.index[0], "date"]) + " to " + str(
                df_chart.at[df_chart.index[-1], "date"]))

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
            ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["side"] == "sell"), color="r", marker="x")
            ax.scatter(x=dfinal.index, y=dfinal["price"].where(dfinal["side"] == "buy"), color="g", marker="x")

        if dfinal.__contains__("capital"):
            ax2 = ax.twinx()
            ax2.plot(dfinal["capital"].where(dfinal["side"] == "sell"), color="#000000", marker="o", markersize=3.5)
            ax2.set_ylabel("Capital")

        plt.figtext(0.5, 0.94,
                    str(pair) + " " + str(timeframe)
                    , fontsize=15, ha="center", bbox={"facecolor": "orange", "alpha": 0.5, "pad": 5})

        plt.figtext(0.01, 0.90,
                    "pair change: " + str(pair_change) + " %" +
                    "\ncapital change: " + str(capital_change) + " %" +
                    "\nwin/loss ration: " + str(win_loss_ratio) +
                    "\naverage winning: " + str(avg_winning_trade) + " %" +
                    "\naverage losing: " + str(avg_losing_trade) + " %"
                    , fontsize=8)

        plt.plot()
        plt.show()

        # fig.savefig(str(save_path) + str(pair.replace('/', '')) + ".jpg", format="jpeg", dpi=300, bbox_inches="tight", pad_inches=0.1)
