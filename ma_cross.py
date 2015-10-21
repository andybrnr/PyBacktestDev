# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 15:31:51 2015

@author: ABerner
"""

# ma_cross.py

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pandas.io.data as web
from backtest import Strategy, Portfolio

class MovingAverageCrossStrategy(Strategy):
    """
    Requires:
    symbol - A stock symbol on which to form a strategy on.
    bars - A DataFrame of bars for the above symbol.
    short_window - Lookback period for short moving average.
    long_window - Lookback period for long moving average."""
    
    def __init__(self, symbol, bars, short_window=100, long_window = 400):
        self.symbol = symbol
        self.bars = bars
        
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self):
        """Returns the DataFrame of symbols containing the signals
        to go long, short or neutral (1, -1 or 0)."""
        signals = pd.DataFrame(index=self.bars.index)
        signals['signal'] = 0.0
        
        # Create the set of short and long simple moving averages over the 
        # respective periods
        signals['short_mavg'] = pd.rolling_mean(self.bars['Close'], self.short_window,
                                                min_periods=self.short_window)
        signals['long_mavg'] = pd.rolling_mean(self.bars['Close'], self.long_window, 
                                                min_periods=self.long_window)
                                                
        # Create a 'signal' (invested or not invested) when the short moving average 
        # crosses the long moving average
        signals.loc[signals['short_mavg']>signals['long_mavg'],'signal'] = 1.0
        signals['positions'] = signals['signal'].diff()
        
        return signals
        
class MarketOnClosePortfolio(Portfolio):
    """Encapsulates the notion of a portfolio of positions based
    on a set of signals as provided by a Strategy.
    
    Requires:
    symbol - A stock symbol which forms the basis of the portfolio.
    bars - A DataFrame of bars for a symbol set.
    signals - A pandas DataFrame of signals (1, 0, -1) for each symbol.
    initial_capital - The amount in cash at the start of the portfolio."""
    
    def __init__(self, symbol, bars, signals, initial_capital=100000.0):
        self.symbol = symbol
        self.bars = bars
        self.signals = signals
        self.initial_capital = float(initial_capital)
        self.positions = self.generate_positions()
        
    def generate_positions(self):
        positions = pd.DataFrame(index=self.signals.index).fillna(0.0)
        positions[self.symbol] = 100*self.signals['signal'] # Buy 100 shares on signal
        return positions
        
    def backtest_portfolio(self):
        pos_diff = self.positions.diff()
        portfolio = pd.DataFrame()
        portfolio['holdings'] = (self.positions.mul(self.bars['Close'],axis=0)).sum(axis=1)
        portfolio['cash'] = self.initial_capital - (pos_diff.mul(self.bars['Close'],axis=0)).sum(axis=1).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['holdings']
        return portfolio
        
if __name__ == "__main__":
    # Obtain daily bars of APL from Yahoo Finance for the period
    # 1st Jan 1990 to 1st Jan 2002 - This is an example from ZipLine
    startDate = pd.datetime(1990,1,1)
    endDate = pd.datetime(2002,1,1)    
    symbol = 'AAPL'
    bars = web.DataReader(symbol, 'yahoo', startDate, endDate)
    
    # Create a Moving Average Cross Strategy instance with a short moving 
    # average window of 100 days and a long window of 400 days
    mac = MovingAverageCrossStrategy(symbol, bars, short_window=100, long_window=400)
    signals = mac.generate_signals()
        
    # Create a portfolio of AAPL, with $100,000 initial capital
    portfolio = MarketOnClosePortfolio(symbol, bars, signals, initial_capital=100000.00)
    returns = portfolio.backtest_portfolio()
    
    # Plot two charts to assess trades and equity curve
    fig = plt.figure()
    fig.patch.set_facecolor('white')     # Set the outer colour to white
    ax1 = fig.add_subplot(211,  ylabel='Price in $')
    
    # Plot the AAPL closing price overlaid with the moving averages
    bars['Close'].plot(ax=ax1, color='r', lw=2.)
    signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)

    # Plot the "buy" trades against AAPL
    ax1.plot(signals.ix[signals.positions == 1.0].index, 
             signals.short_mavg[signals.positions == 1.0],
             '^', markersize=10, color='m')

    # Plot the "sell" trades against AAPL
    ax1.plot(signals.ix[signals.positions == -1.0].index, 
             signals.short_mavg[signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the equity curve in dollars
    ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
    returns['total'].plot(ax=ax2, lw=2.)

    # Plot the "buy" and "sell" trades against the equity curve
    ax2.plot(returns.ix[signals.positions == 1.0].index, 
             returns.total[signals.positions == 1.0],
             '^', markersize=10, color='m')
    ax2.plot(returns.ix[signals.positions == -1.0].index, 
             returns.total[signals.positions == -1.0],
             'v', markersize=10, color='k')

    # Plot the figure
    fig.show()
        
        