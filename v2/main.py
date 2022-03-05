from Exchange import Exchange
from Backtest import Backtest

PAIR = 'BTC/USDT'
TIMEFRAME = '1d'
START = '2017-01-01 00:00:00'
END = '2021-05-01 00:00:00'

exchange = Exchange('binance',
                    '',
                    '')

data = exchange.get_data(PAIR, TIMEFRAME, START, END)

backtest = Backtest(data, PAIR, TIMEFRAME, 1000)

backtest.set_strategy(backtest.high_low_flipper_strategy)
backtest.run()

backtest.get_result()
backtest.plot_result()
