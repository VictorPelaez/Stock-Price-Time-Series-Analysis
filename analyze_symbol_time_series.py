from datetime import date
from dateutil import parser
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
    history[symbol] = []
    for element in symbol_data:
        new_element = []

        # Convert the datetime string
        new_element.append(parser.parse(element[0]))

        # Convert the numeric data
        new_element.extend(map(lambda s : float(s),element[1:]))

        # Add the list back to the history
        history[symbol].append(new_element)
