#region imports
from Classes.ticker import Ticker
from twisted.internet import reactor

import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
from tqdm import tqdm
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


#endregion

# region initialize
client = Client(API_KEY, SECRET_KEY)

pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","SOLUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT"]
tickers = []
for p in pairs:
    p = p.lower() + '@kline_1m'
    tickers.append(p)
# print(tickers)
# tickers = ["btcusdt@kline_1m","ethusdt@kline_1m","dotusdt@kline_1m"]

if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, server status:", status["msg"])
    print("Fetching data.")
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]

    instances = []
    for x in tqdm(range(len(tickers))):
        name = tickers[x][:-9].upper()
        globals()[name] = Ticker(name)
        instances.append(globals()[name]) 
        uppercase_name = name.upper()
        klines = client.get_historical_klines(uppercase_name, interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
        
        for k in klines:
            globals()[name].closes.append(float(k[4]))
            globals()[name].highs.append(float(k[2]))
            globals()[name].lows.append(float(k[3]))
            globals()[name].volumes.append(float(k[5]))
    print(f"Data fetched, you have {total_money} dollar buying power in your spot wallet.")

# endregion

# region functions
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

# order = client.create_order(
#     symbol='BNBBTC',
#     side=SIDE_BUY,
#     type=ORDER_TYPE_LIMIT,
#     timeInForce=TIME_IN_FORCE_GTC,
#     quantity=100,
#     price='0.00001')


def order(side, quantity, symbol,price, order_type=ORDER_TYPE_LIMIT):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity, price=price, timeInForce=TIME_IN_FORCE_IOC,)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

def get_dollar():
    global total_money
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]


# endregion

# main callback function
def process_m_message(msg):
    global total_money
    # print("stream: {} data: {}".format(msg['stream'], msg['data']))
    if msg['data']['e'] == 'error':
        print("error while restarting socket")
    else:
        candle = msg['data']['k']
        candle_closed = candle['x']

        name = msg['data']['s']
        symbol = globals()[name]

        close = candle['c']
        high = candle['h']
        low = candle['l']
        volume = candle['v']

        if candle_closed:
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
                        print(f"You already own {name}.")
                    else:
                        symbol.buy_price = symbol.closes[-1]

                        # calculate how much quantity I can buy
                        if total_money => 20:
                            symbol.amount = 20 / symbol.buy_price
                            symbol.order_succeeded = order(side=SIDE_BUY, quantity=symbol.amount, symbol=name ,order_type=ORDER_TYPE_LIMIT, price=symbol.buy_price)
                            if symbol.order_succeeded:
                                symbol.has_position = True
                                symbol.stop_loss = get_low(symbol.ticker)
                                symbol.log_buy(amount=symbol.amount ,buy_price=symbol.buy_price, ticker=name, money=symbol.money)
                                if float(symbol.stop_loss) > (symbol.buy_price - (symbol.buy_price*0.03)):
                                    symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.03)
                                symbol.take_profit = symbol.buy_price * 1.03
                                print(Fore.GREEN + f"{name} bought rsi: {last_rsi} mfi: {last_mfi}. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}") 
                                get_dollar()

                            symbol.order_succeeded = False

                                          
                        

                        

                # verkoopstrategie
                if symbol.has_position:
                    current_price = symbol.closes[-1]
                    symbol.order_succeeded = False

                    if current_price > float(symbol.take_profit):
                        symbol.order_succeeded = order(side=SIDE_SELL, quantity=symbol.amount, symbol=name ,order_type=ORDER_TYPE_LIMIT,price=current_price)
                        if symbol.order_succeeded:
                            symbol.has_position = False
                            print(Fore.RED + f"{name} sold with a profit.")
                            symbol.log_sell(profit=True ,price=current_price ,ticker=name ,amount=symbol.amount ,money=symbol.money)
                            symbol.amount = 0
                            get_dollar()
                            order_succeeded = False
                        
                    if current_price < float(symbol.stop_loss):
                        symbol.order_succeeded = order(side=SIDE_SELL, quantity=symbol.amount, symbol=name ,order_type=ORDER_TYPE_LIMIT,price=current_price)
                        if symbol.order_succeeded:
                            symbol.has_position = False
                            order_succeeded = False
                            print(Fore.RED  +f"{name} sold with a loss.")
                            symbol.log_sell(profit=False ,price=current_price ,ticker=name ,amount=symbol.amount ,money=symbol.money)
                            symbol.amount = 0
                            get_dollar()
                            order_succeeded = False

                    
                    # else: 
                    #     print(f'{name} was not sold')

                symbol.closes = symbol.closes[-150:]
                symbol.highs = symbol.highs[-150:]
                symbol.lows = symbol.lows[-150:]
                symbol.volumes = symbol.volumes[-150:]
                

bm = BinanceSocketManager(client, user_timeout=600)
conn_key = bm.start_multiplex_socket(tickers, process_m_message)
bm.start() #start the socket manager
