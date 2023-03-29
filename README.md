**Please read if you intend to use the code.**

Version 1 of the backtesting system and trading bot is flawed but is still in the repository because it has more features than version 2.

Version 2 has a fully functional backtesting system and an analysis tool.

I had a hard time figuring out everything, wish ChatGPT existed back then :)

The bot uses the following libraries : pandas, numpy, matplotlib and ccxt.

Below are examples of backtesting output from v2.

![](chart-sample.png)

This is a zoomed-in section of the chart generated. The green crosses indicate where the strategy has bought and the red ones where it has sold. The red line is the stop loss of the current position. This is a simple high-low flipper strategy. The blue line represents the highs and lows with a 50 candle period and the yellow line is an SMA100.

![](summary-example.png)

This is the console output of the same strategy.
