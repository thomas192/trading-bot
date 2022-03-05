import matplotlib.markers as mk
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates
import pandas as pd

import mplfinance as fplt
from mplfinance.original_flavor import candlestick_ohlc
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

        # Plot
        """dfinal = pd.merge(df_chart, df_trades, on="date", how="left")
        fig, ax = plt.subplots()

        if dfinal.__contains__("close"):
            ax.plot(dfinal["close"])
            ax.set_ylabel("Price")
            ax.set_xlabel("From " + str(df_chart.at[df_chart.index[0], "date"]) + " to " + str(
                df_chart.at[df_chart.index[-1], "date"]))

        if dfinal.__contains__("rsi"):
            ax.plot(dfinal["close"].where(dfinal["rsi"] > RSI_HIGH_BAND), color="#17e336")
            ax.plot(dfinal["close"].where(dfinal["rsi"] < RSI_LOW_BAND), color="#e31717")

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
        plt.show()"""

        plt.style.use('ggplot')

        # Format data
        ohlc = df_chart.loc[:, ['date', 'open', 'high', 'low', 'close']]
        ohlc['date'] = pd.to_datetime(ohlc['date'])
        ohlc['date'] = ohlc['date'].apply(mpl_dates.date2num)
        ohlc = ohlc.astype(float)
        if not df_trades.empty:
            df_trades['date'] = pd.to_datetime(df_trades['date'])
            df_trades['date'] = df_trades['date'].apply(mpl_dates.date2num)
            df_trades['date'].astype(float)

        # Create Subplots
        fig, ax = plt.subplots()

        candle_width = 0.0085
        if timeframe == "5m":
            candle_width = candle_width / 3

        candlestick_ohlc(ax, ohlc.values, width=candle_width, colorup='green', colordown='red', alpha=0.8)

        # Set labels & titles
        ax.set_ylabel('Price')
        fig.suptitle(str(pair) + " " + str(timeframe))

        # Format date
        date_format = mpl_dates.DateFormatter('%Y-%m-%d %H:%M:%S')
        ax.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()

        fig.tight_layout()

        if df_trades.__contains__("price"):
            ax.scatter(x=df_trades["date"], y=df_trades["price"].where(df_trades["side"] == "sell"), color="black",
                       marker=mk.CARETDOWN, s=160, zorder=1)
            ax.scatter(x=df_trades["date"], y=df_trades["price"].where(df_trades["side"] == "buy"), color="black",
                       marker=mk.CARETUP, s=160, zorder=1)

        if df_trades.__contains__("capital"):
            ax2 = ax.twinx()
            ax2.plot(df_trades["date"], df_trades["capital"].where(df_trades["side"] == "sell"), color="#03ecfc",
                     marker="D", markersize=3.5)
            ax2.set_ylabel("Capital")

        # Plot bollinger bands
        if df_chart.__contains__("bb_avg"):
            ax.plot(ohlc["date"], df_chart["bb_avg"], color="#8332a8")
        if df_chart.__contains__("bb_low"):
            ax.plot(ohlc["date"], df_chart["bb_low"], color="#8332a8")
        if df_chart.__contains__("bb_up"):
            ax.plot(ohlc["date"], df_chart["bb_up"], color="#8332a8")

        # Plot ichimoku cloud
        if df_chart.__contains__("chikou_span"):
            ax.plot(ohlc["date"], df_chart["chikou_span"], color="#e8e400")
        if df_chart.__contains__("tenkansen"):
            ax.plot(ohlc["date"], df_chart["tenkansen"], color="#00c3ff")
        if df_chart.__contains__("kijunsen"):
            ax.plot(ohlc["date"], df_chart["kijunsen"], color="#a60006")
        if df_chart.__contains__("senkou_a") and df_chart.__contains__("senkou_b"):
            ax.plot(ohlc["date"], df_chart["senkou_a"], color="#00d40e", linewidth=0.5)
            ax.plot(ohlc["date"], df_chart["senkou_b"], color="#d40000", linewidth=0.5)
            x = ohlc["date"]
            y1 = df_chart["senkou_a"]
            y2 = df_chart["senkou_b"]
            ax.fill_between(x, y1, y2, where=y1 < y2, facecolor="#d40000", alpha=0.2)
            ax.fill_between(x, y1, y2, where=y1 > y2, facecolor="#00d40e", alpha=0.2)

        if df_chart.__contains__("short_ema"):
            ax.plot(ohlc["date"], df_chart["short_ema"], color="#ffa600")

        if df_chart.__contains__("long_ema"):
            ax.plot(ohlc["date"], df_chart["long_ema"], color="#33ed09")

        if df_chart.__contains__("sma_50"):
            ax.plot(ohlc["date"], df_chart["sma_50"], color="#ffa600")

        if df_chart.__contains__("sma_200"):
            ax.plot(ohlc["date"], df_chart["sma_200"], color="#ffa600")

        if df_chart.__contains__("vwma"):
            ax.plot(ohlc["date"], df_chart["vwma"], color="#e3d517")

        plt.show()

        # fig.savefig(str(save_path) + str(pair.replace('/', '')) + ".jpg", format="jpeg", dpi=300, bbox_inches="tight", pad_inches=0.1)
