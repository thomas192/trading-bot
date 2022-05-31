from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.dates as dates

from Indicator import Indicator


class Backtest:

    def __init__(self, data, pair, timeframe, equity):
        # Stores price, indicators, and trades for plotting
        self.data = pd.DataFrame(data)
        self.data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        # Stores trades for later analysis
        self.trades = pd.DataFrame(columns=['index', 'buyp', 'sellp', 'change', 'equity'])

        self.pair = pair
        self.timeframe = timeframe
        self.initial_equity = equity
        self.equity = equity

        self.positioned = False
        self.stop_loss = np.nan
        self.buyp = np.nan
        self.sellp = np.nan

        self.trailing_sl = False
        self.expiration = np.nan
        self.bars_left = np.nan
        self.entry = np.nan


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
        if not self.data.__contains__('entry'):
            self.data['entry'] = np.nan
        if not self.data.__contains__('equity'):
            self.data['equity'] = np.nan
            self.data.at[0, 'equity'] = self.initial_equity

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
        prev_entry = self.data.at[prev, 'entry']

        # If an entry is set, check if it's still valid
        if self.entry is not np.nan and not self.positioned:
            # Decrease the number of bars left before expiration
            self.bars_left = self.bars_left - 1
            # If expired reset the entry and the expiration
            if self.bars_left < 0:
                self.entry = np.nan
                self.bars_left = self.expiration
            # Keep track of the entry level for plotting
            else:
                self.data.at[curr, 'entry'] = self.entry

        # Define entry if low went below lfn
        if prev_low < prev_lfn and not self.positioned:
            # Set entry
            self.entry = prev_low + 2 * prev_atr
            # Keep track of the entry level for plotting
            self.data.at[curr, 'entry'] = self.entry
            # Set the number of bars before expiration
            self.bars_left = self.expiration
            return False

        # BUY if entry level has been triggered
        if prev_high > self.entry and self.entry is not np.nan and not self.positioned:
            self.entry = np.nan
            self.bars_left = self.expiration
            # We assume we are not above sma when buying (even if we are)
            self.trailing_sl = False
            # Set stop-loss
            self.stop_loss = open - 2 * prev_atr
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
            self.stop_loss = prev_sma - 1.3 * prev_atr
            self.data.at[curr, 'sl'] = self.stop_loss

        return False


    def set_strategy(self, strategy, expiration):
        self.strategy = strategy
        self.expiration = expiration


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
        self.equity = self.equity + self.equity * change / 100
        self.data.at[i, 'equity'] = self.equity
        row = {'buyp': self.buyp, 'sellp': self.sellp, 'change': change, 'equity': self.equity}
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

        # General
        hodl_return = round((self.data['close'].iloc[-1] - self.data['open'].iloc[0]) / self.data['open'].iloc[0] * 100, 2)
        nb_trades = len(self.trades)
        avg_profit_loss = round(self.trades['change'].mean(), 2)
        net_profit = round((self.equity - self.initial_equity) / self.initial_equity * 100, 2)
        if nb_lost > 0:
            wl_ratio = round(nb_won / nb_lost, 2)
        else:
            wl_ratio = nb_won / 1

        print('\nInitial equity: ' + str(self.initial_equity))
        print('Ending equity: ' + str(self.equity))
        print('Net profit: ' + str(net_profit) + ' %')
        print('Hodl return: ' + str(hodl_return) + ' %')

        print('\n--- ALL TRADES ---')
        print('Number of trades: ' + str(nb_trades))
        print('Average profit/loss: ' + str(avg_profit_loss) + ' %')
        print('Win/loss ratio: ' + str(wl_ratio))

        print('\n--- WINNERS ---')
        print('Total profit: ' + str(total_profit) + ' %')
        print('Average profit: ' + str(avg_profit) + ' %')
        print('Maximum profit: ' + str(max_profit) + ' %')

        print('\n--- LOSERS ---')
        print('Total loss: ' + str(total_loss) + ' %')
        print('Average loss: ' + str(avg_loss) + ' %')
        print('Maximum loss: ' + str(max_loss) + ' %')


    def plot_result(self, display_equity=False):
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
            oline = Line2D(xdata=(indexes[i], indexes[i]-width),
                           ydata=(self.data.at[i, 'open'], self.data.at[i, 'open']),
                           color='black', linewidth=0.5, antialiased=True)
            cline = Line2D(xdata=(indexes[i]+width, indexes[i]),
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
            # Entries
            if self.data.__contains__('entry'):
                ax.plot(self.data['entry'], color='green', linewidth=0.5)
            # Stop-losses
            for i, row in self.data.iterrows():
                if self.data.at[i, 'sl'] != np.nan:
                    ax.add_line(Line2D(xdata=(indexes[i]-2*width, indexes[i]+2*width),
                                       ydata=(self.data.at[i, 'sl'], self.data.at[i, 'sl']),
                                       color='red', linewidth=0.75, antialiased=True))
            # Equity
            if self.data.__contains__('equity') and display_equity:
                ax2 = ax.twinx()
                ax2.plot(self.data['equity'], color='lightgrey', marker='o', linewidth=0.5)
                ax2.set_ylabel('Equity')

        plt.plot()
        plt.show()
