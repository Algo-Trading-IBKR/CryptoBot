#region imports
from Classes.ticker import Ticker
from twisted.internet import reactor

from clickatell.rest import Rest
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

API_KEY = "01rU5GpozT4Owzs0MJNqSIO9KloKJERtpJscOs1gC7gYkcSTWdry4KJYMTl1Sxu4"
SECRET_KEY = "mzYubBy1mRUVElxg2xP4lNAZW76BFDKRxkpDAUJK86pio8FHAxMVxDCCM5AgFPs6"
# Testnet keys
API_KEY_TESTNET = "hmuUZY958uABtMw2JVYI88Dc1CEPIo589bvCTPs6ZEGevQ6Nd7ARzsCdXcapiKof"
SECRET_KEY_TESTNET = "8l1P0MyhNKw8P4Xanr7zTrojFhBTFAoBTKFW5DiUil78kh7zRXtztilje5jQ6RYT"

clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==");
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
bm = BinanceSocketManager(client, user_timeout=600)
log_file = "./StrategyTests/OnePercentStopLossPiramidding"

pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT"]
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
        globals()[name] = Ticker(name, log_file)
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

# endregion

# main callback function
def process_m_message(msg):
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
            # print(Fore.RED + f"{name}")
            symbol.closes.append(float(close))
            symbol.highs.append(float(high))
            symbol.lows.append(float(low))
            symbol.volumes.append(float(volume))

            if len(symbol.closes) > rsi_period:
                rsi = talib.RSI(np.array(symbol.closes), timeperiod=rsi_period)
                mfi = talib.MFI(np.array(symbol.highs), np.array(symbol.lows), np.array(symbol.closes), np.array(symbol.volumes), timeperiod=mfi_period)

                last_rsi = rsi[-1]
                last_mfi = mfi[-1]
                # print(Fore.GREEN + f"{name} . rsi: {last_rsi} mfi: {last_mfi}.")

                # koopstrategie
                if last_rsi < rsi_oversold and last_mfi < mfi_oversold:
                    if symbol.has_position:
                        print(f"You already own {name}.")
                    else:
                        symbol.buy_price = symbol.closes[-1]
                        symbol.average_price = symbol.buy_price

                        # calculate how much quantity I can buy
                        symbol.position = (symbol.money/2)/symbol.buy_price
                        symbol.stop_loss = get_low(symbol.ticker)
                        symbol.money -= symbol.position * symbol.average_price
                        symbol.log_buy(amount=symbol.position ,buy_price=symbol.buy_price, ticker=name, money=symbol.money)

                        

                        if float(symbol.stop_loss) > (symbol.buy_price - (symbol.buy_price*0.03)):
                            symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.03)
                        # symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.03)
                        symbol.take_profit = symbol.buy_price * 1.012
                        symbol.order_succeeded = True

                        if symbol.order_succeeded:
                            print(Fore.GREEN + f"{name} bought for {symbol.buy_price} dollar. rsi: {last_rsi} mfi: {last_mfi}. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                            try:
                                response = clickatell.sendMessage(to=['32470579542'], message=f"{name} bought for {symbol.buy_price} dollar.")
                            except Exception as e:
                                pass
                            symbol.has_position = True
                            symbol.order_succeeded = False

                # verkoopstrategie
                if symbol.has_position:
                    current_price = symbol.closes[-1]
                    symbol.order_succeeded = False
                    # print(name, f" -> {current_price}")

                    if current_price > float(symbol.take_profit):
                        print(Fore.RED + f"{name} sold with a profit.")
                        symbol.money += symbol.position * current_price
                        try:
                            response = clickatell.sendMessage(to=['32470579542'], message=f"{name} sold with a profit. money left: {symbol.money}.")
                        except Exception as e:
                            pass
                        symbol.log_sell(profit=True ,price=current_price ,ticker=name ,amount=symbol.position ,money=symbol.money)
                        symbol.order_succeeded = True
                        symbol.position = 0
                        if symbol.order_succeeded:
                            symbol.has_position = False
                            order_succeeded = False


                    if current_price < float(symbol.stop_loss):
                        if float(symbol.money) > 20:
                            print(Fore.RED  +f"{name} price dropped under the stop loss, buy a second time")
                            symbol.buy_price = symbol.closes[-1]
                            amount = symbol.money/symbol.buy_price                   
                            symbol.log_buy(amount=amount ,buy_price=symbol.buy_price, ticker=name, money=symbol.money)
                            symbol.position += amount
                            symbol.average_price = 100/ symbol.position
                            symbol.stop_loss = get_low(symbol.ticker)
                            if float(symbol.stop_loss) > (symbol.buy_price - (symbol.buy_price*0.05)):
                                symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.05)
                            # symbol.stop_loss = symbol.buy_price - (symbol.buy_price*0.03)
                            symbol.money -= symbol.buy_price * amount
                            symbol.take_profit = symbol.average_price * 1.012
                            symbol.order_succeeded = True

                            if symbol.order_succeeded:
                                print(Fore.GREEN + f"{name} bought for {symbol.buy_price} dollar.")
                                try:
                                    response = clickatell.sendMessage(to=['32470579542'], message=f"SECOND BUY: {name} bought for {symbol.buy_price} dollar.")
                                except Exception as e:
                                    pass
                                symbol.has_position = True
                                symbol.order_succeeded = False

                        else: 
                            print(Fore.RED  +f"{name} sold with a loss.")
                            symbol.money += symbol.position * current_price
                            try:
                                response = clickatell.sendMessage(to=['32470579542'], message=f"{name} sold with a loss. money left: {symbol.money}.")
                            except Exception as e:
                                pass     
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
                

# start the sockets
if str(client.ping()) == '{}':
    conn_key = bm.start_multiplex_socket(tickers, process_m_message)
    bm.start() #start the socket manager
