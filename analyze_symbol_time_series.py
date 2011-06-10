import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab   as mlab
import matplotlib.ticker as ticker
from datetime    import date
from dateutil    import parser
from ystockquote import *

# Load the symbols to analyze
f = open('symbols.txt','r')
symbols = f.readlines()
symbols = map(lambda s : s[:-1],symbols)
f.close()

# Download the history for each symbol
history = {}
for symbol in symbols:
    history[symbol] = get_historical_prices(symbol,'19000101',date.today().strftime('%Y%m%d'))
    
    # Get the symbol data and remove the field labels
    symbol_data = history[symbol][1:]

    # Convert string data to properly typed data
    history[symbol] = history[symbol][:1]
    for element in symbol_data:
        new_element = []

        # Convert the datetime string
        new_element.append(parser.parse(element[0]))

        # Convert the numeric data
        new_element.extend(map(lambda s : float(s),element[1:]))

        # Add the list back to the history
        history[symbol].append(new_element)

# Compute 50 day moving averages of closing price
fifty_day_ma_history = {}
for symbol in symbols:
    fifty_day_ma_history[symbol] = []

    # Get closing price history for symbol
    closing_prices = map(lambda e : e[4], history[symbol][1:])

    # Compute moving averages
    fifty_day_window = closing_prices[:50]
    for i in xrange(len(closing_prices)-49):
        fifty_day_ma_history[symbol].append(sum(fifty_day_window)/50.0)

        # Update the window as necessary
        if i < len(closing_prices)-50:
            del fifty_day_window[0]
            fifty_day_window.append(closing_prices[50+i])

# Compute 3 month, 6 month and 1 year performance based on smoothed closing prices
# along with the relative strength. Will use 13 week, 26 week and 52 week lags for 
# computations. Relative strength is defined here as the average of the 3 month, 
# 6 month and 1 year performance.
performance = {}
for symbol in symbols:
    symbol_perf = {}
    smoothed_price = fifty_day_ma_history[symbol]
    symbol_perf['3mo'] = (smoothed_price[0] - smoothed_price[5*13]) / smoothed_price[5*13]
    symbol_perf['6mo'] = (smoothed_price[0] - smoothed_price[5*26]) / smoothed_price[5*26]
    symbol_perf['1yr'] = (smoothed_price[0] - smoothed_price[5*52]) / smoothed_price[5*52]
    symbol_perf['rs']  = (symbol_perf['3mo'] + symbol_perf['6mo'] + symbol_perf['1yr']) / 3.0
    performance[symbol] = symbol_perf

# Sort the symbols based on relative strength
rs = []
for symbol in symbols:
    rs.append((symbol,performance[symbol]['rs']))
rs.sort(key = lambda tup : tup[1],reverse = True)
rs_ordered_symbols = map(lambda tup : tup[0],rs)

# Print out the performance figures
print "3 MO\t6 MO\t1 YR\tRS\t50DAY\t200DAY\tBUY\tSYMB"
for symbol in rs_ordered_symbols:

    # Add the performance numbers to the display string
    keys = ['3mo','6mo','1yr','rs']
    s = ''
    for key in keys:
        s += "%.1f\t" % (performance[symbol][key]*100.0)
    fifty = float(get_50day_moving_avg(symbol))
    twohund = float(get_200day_moving_avg(symbol))
    s += "%.2f\t%.2f\t" % (fifty,twohund)

    # Check to see if the 50 day moving average is above the 200 day moving average
    if fifty > twohund:
        s += "YES\t"
    else:
        s += "NO\t"

    # Add the symbol label
    s += "%s" % symbol
    print s

# Plot the fifty day moving averages
for symbol in rs_ordered_symbols:

    # Get the moving average history
    ma_history = fifty_day_ma_history[symbol]
    N = len(ma_history)

    # Get the closing prices
    closing_prices = map(lambda e : e[4], history[symbol][1:])

    # Remove the last 49 days of price information so that the closing
    # price list is as long as the moving average list
    closing_prices = closing_prices[:-49]

    # Create the indices
    ind = np.arange(N)
    dates = map(lambda tup : tup[0],history[symbol][1:N+1])

    # Reverse the lists so the oldest data is first
    dates.reverse()
    ma_history.reverse()
    closing_prices.reverse()

    def format_date(x, pos=None):
        thisind = np.clip(int(x+0.5), 0, N-1)
        return dates[thisind].strftime('%Y-%m-%d')

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(ind, closing_prices)
    ax.plot(ind, ma_history, 'r--')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_date))
    fig.autofmt_xdate()
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('Symbol: %s' % symbol)
    plt.grid()
    plt.draw()
    

