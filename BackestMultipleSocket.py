#region imports
# own classes
from Classes.ticker import Ticker

# libraries
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
import numpy as np
import logging 


#endregion
#region variables

API_KEY = "hKclENu75kFYky6xVXxHqVNzdzOQc0RAZ5kElzJggmF3N2EQDn4XjP2XPhHtbxjI"
SECRET_KEY = "2albG5h0FVjUpvIjg1aQvoVXH6sDgUvWsMmyzkajjaPkIrHaKUYUVgvraC86a7iS"
# Testnet keys
API_KEY_TESTNET = "hmuUZY958uABtMw2JVYI88Dc1CEPIo589bvCTPs6ZEGevQ6Nd7ARzsCdXcapiKof"
SECRET_KEY_TESTNET = "8l1P0MyhNKw8P4Xanr7zTrojFhBTFAoBTKFW5DiUil78kh7zRXtztilje5jQ6RYT"

# rsi
rsi_period = 14
rsi_overbought = 80
rsi_oversold = 20

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12
#endregion




tickers = ["BNBUSDT", "DOGEUSDT", "XRPUSDT", "LITUSDT", "CAKEUSDT", "OMGUSDT", "REEFUSDT", "DODOUSDT", "RVNUSDT"]
client = Client(API_KEY, SECRET_KEY)

logging.basicConfig(filename="./Logs/Test.log", format='%(asctime)s %(message)s', filemode='a') 
logger=logging.getLogger() 
logger.setLevel(logging.INFO) 


if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, status server: ", status["msg"])
    print("data ophalen")

    instances = []
    for x in range(len(tickers)):
        globals()[tickers[x]] = Ticker(tickers[x])
        instances.append(globals()[tickers[x]]) 
        klines = client.get_historical_klines(tickers[x], interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')

        for k in klines:
            globals()[tickers[x]].closes.append(float(k[4]))
            globals()[tickers[x]].highs.append(float(k[2]))
            globals()[tickers[x]].lows.append(float(k[3]))
            globals()[tickers[x]].volumes.append(float(k[5]))

    for i in instances:
        print(i.ticker, 'Object aangemaakt')

    print("data opgehaald")
    

def process_message(msg):
    name = msg['s']
    symbol = globals()[name]

    change_in_price = get_change(symbol.ticker) #ticker
    candle = msg['k']
    candle_closed = candle['x']

    close = candle['c']
    high = candle['h']
    low = candle['l']
    volume = candle['v']
            
    if candle_closed:
        print(symbol.ticker, " -> candle closed at: ", close)
        symbol.closes.append(float(close))
        symbol.highs.append(float(high))
        symbol.lows.append(float(low))
        symbol.volumes.append(float(volume))
     
        if len(symbol.closes) > rsi_period:
            rsi = talib.RSI(np.array(symbol.closes), timeperiod=rsi_period)
            mfi = talib.MFI(np.array(symbol.highs), np.array(symbol.lows), np.array(symbol.closes), np.array(symbol.volumes), timeperiod=mfi_period)
            
            last_rsi = rsi[-1]
            last_mfi = mfi[-1]

            # koopstrategie
            if last_rsi < rsi_oversold and last_mfi < mfi_oversold:
                if symbol.has_position:
                    print(f"Je hebt {name} momenteel al.")
                else:
                    print(f"{name} is oversold. Placing order.")
                    logger.info(f"bought {name} at {buy_price}")

                    symbol.buy_price = symbol.closes[-1]
                    symbol.stop_loss = get_low(symbol.ticker)

                    if symbol.stop_loss < (symbol.buy_price - (symbol.buy_price*0.02)):
                        symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.02)
                    symbol.take_profit = symbol.buy_price * 1.03                   
                    symbol.order_succeeded = True

                    if symbol.order_succeeded:
                        symbol.has_position = True
                        symbol.order_succeeded = False

            # verkoopstrategie
            if symbol.has_position:
                current_price = symbol.closes[-1]
                symbol.order_succeeded = False

                if current_price > symbol.take_profit:
                    print("sold with profit")
                    logger.info(f"PROFIT, Sold {name} at {current_price}")
                    symbol.order_succeeded = True

                if current_price < symbol.stop_loss:
                    print("sold at loss")
                    logger.info(f"LOSS, Sold {name} at {current_price}")
                    symbol.order_succeeded = True

                if symbol.order_succeeded:
                    symbol.has_position = False
                    order_succeeded = False
                else: 
                    print('was not sold')

            symbol.closes = symbol.closes[-150:]
            symbol.highs = symbol.highs[-150:]
            symbol.lows = symbol.lows[-150:]
            symbol.volumes = symbol.volumes[-150:]
                


def get_change(ticker):
    data = client.get_ticker(symbol=ticker)
    change = data["priceChangePercent"]
    # print(ticker, " change in price: ", change)
    return change

def get_low(ticker):
    data = client.get_ticker(symbol=ticker)
    low = data["lowPrice"]
    # print(ticker, " change in price: ", change)
    return low

    
#create the websockets
bm = BinanceSocketManager(client, user_timeout=60)


for i in instances:
    conn_key = bm.start_kline_socket(symbol=i.ticker, callback=process_message, interval=KLINE_INTERVAL_1MINUTE)

bm.start() #start the socket manager
