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
from colorama import Fore, Back, Style,init
init(autoreset=True)

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
rsi_oversold = 19

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12

percentage = 0
#endregion

# tickers = ["BNBUSDT", "DOGEUSDT", "XRPUSDT", "LITUSDT", "CAKEUSDT", "OMGUSDT", "REEFUSDT", "DODOUSDT", "RVNUSDT"]
tickers = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","SOLUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT"]
# tickers = ["BNBUSDT"]
client = Client(API_KEY, SECRET_KEY)


if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, server status:", status["msg"])
    print("Fetching data.")
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]

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
        percentage += (100 / len(tickers))
        print(f'{percentage:.0f}% loaded in')
    print(f"Data fetched, you have {total_money} dollar buying power in your spot wallet.")

    

def process_message(msg):
    #ticker
    if msg['e'] == 'error':
        print('error: ', msg)
    else:
        candle = msg['k']
        candle_closed = candle['x']

        name = msg['s']
        symbol = globals()[name]

        change_in_price = get_change(symbol.ticker) 

        close = candle['c']
        high = candle['h']
        low = candle['l']
        volume = candle['v']

        if candle_closed:
            # print(msg)
            symbol.closes.append(float(close))
            symbol.highs.append(float(high))
            symbol.lows.append(float(low))
            symbol.volumes.append(float(volume))

            if len(symbol.closes) > rsi_period:
                rsi = talib.RSI(np.array(symbol.closes), timeperiod=rsi_period)
                mfi = talib.MFI(np.array(symbol.highs), np.array(symbol.lows), np.array(symbol.closes), np.array(symbol.volumes), timeperiod=mfi_period)

                last_rsi = rsi[-1]
                last_mfi = mfi[-1]

                # print(symbol.ticker, " -> candle closed at: ", close, " with rsi: ",last_rsi ," and mfi: ", last_mfi)

                # koopstrategie
                if last_rsi < rsi_oversold and last_mfi < mfi_oversold:
                    if symbol.has_position:
                        print(f"you already own {name}.")
                    else:

                        symbol.buy_price = symbol.closes[-1]

                        # calculate how much quantity I can buy
                        symbol.position = symbol.money/symbol.buy_price
                        symbol.stop_loss = get_low(symbol.ticker)
                        symbol.log_buy(amount=symbol.position ,buy_price=symbol.buy_price, ticker=name, money=symbol.money)
                        symbol.money = 0


                        if float(symbol.stop_loss) > (symbol.buy_price - (symbol.buy_price*0.03)):
                            symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.03)
                        symbol.take_profit = symbol.buy_price * 1.03                   
                        symbol.order_succeeded = True
                        
                        if symbol.order_succeeded:
                            print(Fore.GREEN + f"{name} bought rsi: {last_rsi} mfi: {last_mfi}. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")

                            symbol.has_position = True
                            symbol.order_succeeded = False

                # verkoopstrategie
                if symbol.has_position:
                    current_price = symbol.closes[-1]
                    symbol.order_succeeded = False

                    if current_price > float(symbol.take_profit):
                        print(Fore.RED + f"{name} sold with a profit.")
                        symbol.money = symbol.position * current_price
                        symbol.log_sell(profit=True ,price=current_price ,ticker=name ,amount=symbol.position ,money=symbol.money)
                        symbol.order_succeeded = True
                        symbol.position = 0


                    if current_price < float(symbol.stop_loss):
                        print(Fore.RED  +f"{name} sold with a loss.")
                        symbol.money = symbol.position * current_price
                        symbol.log_sell(profit=False ,price=current_price ,ticker=name ,amount=symbol.position ,money=symbol.money)
                        symbol.order_succeeded = True
                        symbol.position = 0

                    if symbol.order_succeeded:
                        symbol.has_position = False
                        order_succeeded = False
                    # else: 
                    #     print(f'{name} was not sold')

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
bm = BinanceSocketManager(client, user_timeout=600)


for i in instances:
    conn_key = bm.start_kline_socket(symbol=i.ticker, callback=process_message, interval=KLINE_INTERVAL_1MINUTE)

bm.start() #start the socket manager
