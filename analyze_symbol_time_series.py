import numpy as np
import matplotlib.pyplot as plt
from datetime    import date
from dateutil    import parser
from math        import sqrt
from matplotlib.backends.backend_pdf import PdfPages
from ystockquote import *
from gmail import *

def simple_moving_average(price_history,days):
    ma_history = np.zeros(len(price_history)-days+1)
    window = list(price_history[:days])
    for i in xrange(len(price_history)-days+1):
        ma_history[i] = sum(window)/float(days)

        # Update the window as necessary
        if i < len(price_history)-days:
            del window[0]
            window.append(price_history[days+i])
    
    return ma_history
    
def exponential_moving_average(price_history,days):
    alpha = 2/float(days+1)
    ma_history = np.zeros(len(price_history))
    
    # Filter the price history under the assumption that the history 
    # begins with the most recent price data
    ma_prev = price_history[-1]
    ma_history[-1] = price_history[-1]
    for i in xrange(len(price_history)-2,-1,-1):
        ma_history[i] = (1-alpha)*ma_prev + alpha*price_history[i]
        ma_prev = ma_history[i]
        
    return(ma_history)
    
def bollinger_bands(price_history):
    # Compute the 20 day simple moving average for the middle band
    middle_band = simple_moving_average(price_history,20)
    
    # Compute the squared deviations from the middle band
    sq_deviations = np.zeros(len(middle_band))
    for i in xrange(len(middle_band)):
        sq_deviations[i] = pow(price_history[i]-middle_band[i],2)

    # Compute the 20 day simple moving average of the squared deviations 
    std_deviations = simple_moving_average(sq_deviations,20)
    
    # Take the square root to get the standard deviations
    std_deviations = np.array(map(sqrt,std_deviations))
    
    return [middle_band,std_deviations]

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

# Compute 50 and 200 day moving averages of closing price
fifty_day_ma_history = {}
twohund_day_ma_history = {}
for symbol in symbols:

    # Get closing price history for symbol - latest price data occurs earliest in list
    closing_prices = map(lambda e : e[4],history[symbol][1:])

    # Compute moving averages
    fifty_day_ma_history[symbol] = simple_moving_average(closing_prices,50)
    twohund_day_ma_history[symbol] = simple_moving_average(closing_prices,200)

# Compute 3 month, 6 month and 1 year performance based on smoothed closing prices
# along with the relative strength. Will use 13 week, 26 week and 52 week lags for 
# computations. Relative strength is defined here as the average of the 3 month, 
# 6 month and 1 year performance as suggested in "The Ivy Portfolio".
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
num_ma_crossings = 0
stats = "3 MO\t6 MO\t1 YR\tRS\t50DAY\t200DAY\tBUY\tCHNG\tSYMB\n"
for symbol in rs_ordered_symbols:

    # Add the performance numbers to the display string
    keys = ['3mo','6mo','1yr','rs']
    for key in keys:
        stats += "%.1f\t" % (performance[symbol][key]*100.0)
    fifty = fifty_day_ma_history[symbol][0] 
    twohund = twohund_day_ma_history[symbol][0] 
    stats += "%.2f\t%.2f\t" % (fifty,twohund)

    # Check to see if the 50 day moving average is above the 200 day moving average
    if fifty > twohund:
        stats += "YES\t"
    else:
        stats += "NO\t"

    # Check to see if the 50 day and 200 day moving averages just crossed
    # TODO: Might want to check to see if a crossing has happened in the last seven days
    prev_fifty = fifty_day_ma_history[symbol][1]
    prev_twohund = twohund_day_ma_history[symbol][1]
    if (fifty-twohund)*(prev_fifty-prev_twohund) < 0:
        stats += "YES\t"
        num_ma_crossings += 1
    else:
        stats += "NO\t"

    # Add the symbol label
    stats += "%s\n" % symbol

print stats

# Plot the price and moving average histories
pp = PdfPages('figures.pdf')
for symbol in rs_ordered_symbols:

    # Get the moving average histories
    fd_ma_history = fifty_day_ma_history[symbol]
    thd_ma_history = twohund_day_ma_history[symbol]

    # Get the dates and closing prices
    dates = map(lambda tup : tup[0],history[symbol][1:])
    closing_prices = map(lambda tup : tup[4],history[symbol][1:])

    # Compute the Bollinger bands
    [middle_band,std_deviations] = bollinger_bands(closing_prices)
    upper_band = middle_band[:len(std_deviations)] + 2*std_deviations
    lower_band = middle_band[:len(std_deviations)] - 2*std_deviations
    
    # Reverse the lists so the oldest data is first
    dates.reverse()
    fd_ma_history  = fd_ma_history[::-1]
    thd_ma_history = thd_ma_history[::-1]
    closing_prices = closing_prices[::-1]
    middle_band    = middle_band[::-1]
    upper_band     = upper_band[::-1]
    lower_band     = lower_band[::-1]

    # Generate the plot
    price_history_days = len(closing_prices)
    plt.figure()
    plt.plot(closing_prices,label='Closing Price')
    plt.plot(range(19,price_history_days),middle_band,'c',label='20 Day MA')
    plt.plot(range(38,price_history_days),upper_band,'c--')
    plt.plot(range(38,price_history_days),lower_band,'c--')    
    plt.plot(range(49,price_history_days),fd_ma_history,label='50 Day MA',color='r')
    plt.plot(range(199,price_history_days),thd_ma_history,label='200 Day MA',color='g')
    plt.legend(loc='lower left')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.title('Symbol: %s' % symbol)
    plt.grid()
    plt.draw()
    
    # Save plot to the PDF file
    pp.savefig()

# Close the PDF file
pp.close()

# Write out the performance results to a text file
f = open('performance.txt','w')
f.write(stats)
f.close()

# Load email credentials
f = open('credentials.txt','r')
cred = f.readlines()
f.close()
cred = map(lambda s : s[:-1],cred)
user,password = cred

# Load recipients
f = open('recipients.txt','r')
addresses = f.readlines()
f.close()
addresses = map(lambda s : s[:-1],addresses)

# Email the results
text = 'Number of moving average crossings today: %d\n\n' % num_ma_crossings
for recipient in addresses:
    send_mail('Ivy Portfolio Metrics',text,['performance.txt','figures.pdf'],user,password,recipient)
