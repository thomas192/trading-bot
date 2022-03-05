from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.dates as dates

from Indicator import Indicator


class Backtest:

    def __init__(self, data, pair, timeframe, capital):
        # Stores price, indicators, and trades for plotting
        self.data = pd.DataFrame(data)
        self.data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        # Stores trades for later analysis
        self.trades = pd.DataFrame(columns=['index', 'buyp', 'sellp', 'change', 'capital'])

        self.pair = pair
        self.timeframe = timeframe
        self.initial_capital = capital
        self.capital = capital

        self.positioned = False
        self.stop_loss = np.nan
        self.buyp = np.nan
        self.sellp = np.nan

        self.trailing_sl = False


    def high_low_flipper_strategy(self, curr):
        if not self.data.__contains__('hfn'):
            Indicator.add_indicator(self.data, 'hfn', 'hfn', 50)
        if not self.data.__contains__('lfn'):
            Indicator.add_indicator(self.data, 'lfn', 'lfn', 50)
        if not self.data.__contains__('atr'):
            Indicator.add_indicator(self.data, 'atr', 'atr', 20)
        if not self.data.__contains__('sma'):
            Indicator.add_indicator(self.data, 'sma', 'sma', 100)

        if not self.data.__contains__('buyp'):
            self.data['buyp'] = np.nan
        if not self.data.__contains__('sellp'):
            self.data['sellp'] = np.nan
        if not self.data.__contains__('sl'):
            self.data['sl'] = np.nan

        open = self.data.at[curr, 'open']
        prev = curr - 1
        prev_open = self.data.at[prev, 'open']
        prev_high = self.data.at[prev, 'high']
        prev_low = self.data.at[prev, 'low']
        prev_close = self.data.at[prev, 'close']
        prev_hfn = self.data.at[prev, 'hfn']
        prev_lfn = self.data.at[prev, 'lfn']
        prev_atr = self.data.at[prev, 'atr']
        prev_sma = self.data.at[prev, 'sma']

        # BUY at open if low went below lfn
        if prev_low < prev_lfn and not self.positioned:
            # We assume we are not above sma when buying (even if we are)
            self.trailing_sl = False
            # Set stop-loss
            self.stop_loss = open - 1.2 * prev_atr
            self.data.at[curr, 'sl'] = self.stop_loss
            return {'side': 'buy', 'price': open}

        # If high goes above hfn
        if prev_high > prev_hfn and self.positioned:
            # SELL if below sma
            if prev_high < prev_sma:
                return {'side': 'sell', 'price': open}
            # Hold position and set trailing stop-loss
            else:
                self.trailing_sl = True

        # Set trailing stop-loss below sma
        if self.trailing_sl and self.positioned:
            self.stop_loss = prev_sma - 1.2 * prev_atr
            self.data.at[curr, 'sl'] = self.stop_loss

        return False


    def set_strategy(self, strategy):
        self.strategy = strategy


    def run(self):
        for curr, row in self.data.iterrows():
            if curr > 0:
                prev = curr - 1
                # Check if stop-loss was hit
                if self.data.at[prev, 'low'] < self.stop_loss and self.positioned:
                    self.sellp = self.stop_loss
                    self.data.at[prev, 'sellp'] = self.sellp
                    # Reset
                    self.positioned = False
                    self.stop_loss = np.nan
                    # Save trade
                    self.save_trade(prev)

                else:
                    # Get action
                    action = self.strategy(curr)
                    if action is not False:
                        if action['side'] == 'buy':
                            self.buyp = action['price']
                            self.data.at[curr, 'buyp'] = self.buyp
                            self.positioned = True

                        elif action['side'] == 'sell':
                            self.sellp = action['price']
                            self.data.at[curr, 'sellp'] = self.sellp
                            # Reset
                            self.positioned = False
                            self.stop_loss = np.nan
                            # Save trade
                            self.save_trade(curr)


    def save_trade(self, i):
        change = (self.sellp - self.buyp) / self.buyp * 100
        change = change - 2 * 0.075
        self.capital = self.capital + self.capital * change / 100
        row = {'index': i, 'buyp': self.buyp, 'sellp': self.sellp, 'change': change, 'capital': self.capital}
        self.trades = self.trades.append(row, ignore_index=True)


    def get_result(self):
        # Winners
        won = self.trades[self.trades['change'] > 0]
        nb_won = len(won)
        total_profit = round(won['change'].sum(), 2)
        avg_profit = round(won['change'].mean(), 2)
        max_profit = round(won['change'].max(), 2)

        # Losers
        lost = self.trades[self.trades['change'] < 0]
        nb_lost = len(lost)
        total_loss = round(lost['change'].sum(), 2)
        avg_loss = round(lost['change'].mean(), 2)
        max_loss = round(lost['change'].min(), 2)

        # All trades
        nb_trades = len(self.trades)
        avg_profit_loss = round(self.trades['change'].mean(), 2)
        net_profit = round((self.capital - self.initial_capital) / self.initial_capital * 100, 2)
        if nb_lost > 0:
            wl_ratio = round(nb_won / nb_lost, 2)
        else:
            wl_ratio = nb_won / 1

        print('\nInitial capital: ' + str(self.initial_capital))
        print('Ending capital: ' + str(self.capital))
        print('Net profit: ' + str(net_profit))

        print('\n--- ALL TRADES ---')
        print('Number of trades: ' + str(nb_trades))
        print('Average profit/loss: ' + str(avg_profit_loss))
        print('Win/loss ratio: ' + str(wl_ratio))

        print('\n--- WINNERS ---')
        print('Total profit: ' + str(total_profit))
        print('Average profit: ' + str(avg_profit))
        print('Maximum profit: ' + str(max_profit))

        print('\n--- LOSERS ---')
        print('Total loss: ' + str(total_loss))
        print('Average loss: ' + str(avg_loss))
        print('Maximum loss: ' + str(max_loss))


    def plot_result(self):
        fig, ax = plt.subplots()
        
        # Title
        plt.figtext(0.5, 0.94, self.pair + ' ' + self.timeframe, fontsize=15, ha='center')

        indexes = self.data.index.values.tolist()
        if self.timeframe == '1d': # The width of the bar for open and close
            width = 0.35
        elif self.timeframe == '4h':
            width = 0.06

        # Plot price action
        for i, row in self.data.iterrows():
            # Draw bars
            vline = Line2D(xdata=(indexes[i], indexes[i]),
                           ydata=(self.data.at[i, 'low'], self.data.at[i, 'high']),
                          color='black', linewidth=0.5, antialiased=True)
            oline = Line2D(xdata=(indexes[i], indexes[i]+width),
                           ydata=(self.data.at[i, 'open'], self.data.at[i, 'open']),
                           color='black', linewidth=0.5, antialiased=True)
            cline = Line2D(xdata=(indexes[i]-width, indexes[i]),
                           ydata=(self.data.at[i, 'close'], self.data.at[i, 'close']),
                           color='black', linewidth=0.5, antialiased=True)
            # Add bars
            ax.add_line(vline)
            ax.add_line(oline)
            ax.add_line(cline)
            ax.autoscale_view()

        ax.set_ylabel('Price')
        ax.set_xlabel(datetime.strptime(self.data.at[self.data.index[0], 'date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y')
                      + ' to ' + datetime.strptime(self.data.at[self.data.index[-1], 'date'], '%Y-%m-%d %H:%M:%S.%f').strftime('%d-%m-%Y'))

        # Plot indicators
        if self.data.__contains__('hfn'):
            ax.plot(self.data['hfn'], color='blue', linewidth=0.5)
        if self.data.__contains__('lfn'):
            ax.plot(self.data['lfn'], color='blue', linewidth=0.5)
        if self.data.__contains__('sma'):
            ax.plot(self.data['sma'], color='orange', linewidth=0.75)

        # Plot trades
        if self.data.__contains__('buyp'):
            # Signals
            ax.scatter(x=indexes, y=self.data['buyp'], color='g', marker='x')
            ax.scatter(x=indexes, y=self.data['sellp'], color='r', marker='x')
            # Stop-losses
            for i, row in self.data.iterrows():
                if self.data.at[i, 'sl'] != np.nan:
                    ax.add_line(Line2D(xdata=(indexes[i]-2*width, indexes[i]+2*width),
                                       ydata=(self.data.at[i, 'sl'], self.data.at[i, 'sl']),
                                       color='red', linewidth=0.75, antialiased=True))

        plt.plot()
        plt.show()
