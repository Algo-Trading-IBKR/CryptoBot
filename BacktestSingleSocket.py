#region imports
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

#indicator vars
TRADE_SYMBOL = 'LITUSDT'
TRADE_QUANTITY = 15

# rsi
rsi_period = 11
rsi_overbought = 80
rsi_oversold = 20

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12

stop_loss = 2
take_profit = 3
money = 100

limit_lost = 1000
limit_profit = 0
highs = []
lows = []
volumes = []
closes = []
has_position = False
#endregion

#region initialize client
# client aanmaken
logging.basicConfig(filename="./Logs/First.log", format='%(asctime)s %(message)s', filemode='a') 

client = Client(API_KEY, SECRET_KEY)

logger=logging.getLogger() 
logger.setLevel(logging.INFO) 


if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, status server: ", status["msg"])
    # info = client.get_exchange_info()
    # symbol_info = client.get_symbol_info('BNBUSDT')
    # depth = client.get_order_book(symbol='BNBUSDT')
    # avg_price = client.get_avg_price(symbol='BNBUSDT')
    # tickers = client.get_ticker()
    # account_info = client.get_account()
    balance = client.get_asset_balance(asset='USDT')
    LIT = client.get_asset_balance(asset='LIT')
    # trades = client.get_my_trades(symbol='BNBUSDT')
    print(f"Je hebt {balance['free']} USDT en {LIT['free']} LIT")
    print("data ophalen")
    klines = client.get_historical_klines("LITUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
    for kline in klines:
        closes.append(float(kline[4]))
        highs.append(float(kline[2]))
        lows.append(float(kline[3]))
        volumes.append(float(kline[5]))
    print("data opgehaald")
#endregion

# order for binance
def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print("send order to binance")
        # order = client.create_order(symbol=symbol, side=side,type=order_type, quantity=quantity)
        # print(order)
        print("trying to: ", side)
    except Exception as e:
        print("error: ", e)
        return False
    return True


def process_message(msg):
    global closes, highs, lows, volumes, has_position, limit_lost,limit_profit
    candle = msg['k']
    candle_closed = candle['x']

    close = candle['c']
    high = candle['h']
    low = candle['l']
    volume = candle['v']

    symbol = msg['s']
    
    if candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        volumes.append(float(volume))

        if len(closes) > rsi_period:
            np_closes = np.array(closes)
            np_highs = np.array(highs)
            np_lows = np.array(lows)
            np_volumes = np.array(volumes)

            rsi = talib.RSI(np_closes, rsi_period)
            mfi = talib.MFI(np_highs, np_lows, np_closes, np_volumes, timeperiod=mfi_period)
            # macd, macdsignal, macdhist = talib.MACD(np_closes, fastperiod=12, slowperiod=26, signalperiod=9)
            # last_macdhist = macdhist[-1]
            last_rsi = rsi[-1]
            last_mfi = mfi[-1]
            print(f'mfi: {last_mfi}, rsi: {last_rsi}.')
            
            # KOPEN
            if last_rsi < rsi_oversold and last_mfi < mfi_oversold:
                if has_position:
                    print("You already own this ticker")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    buy_price = np_closes[-1]
                    limit_lost = buy_price-(buy_price*(stop_loss/100))
                    limit_profit = buy_price *(1 + (take_profit/100))
                    logger.info(f"bought at {buy_price}") 

                    # Binance buy order
                    # order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    order_succeeded = True
                    if order_succeeded:
                        has_position = True
            
            # VERKOPEN
            if has_position:
                # prev_price = np_closes[-2]
                current_price = np_closes[-1]
                
                #binance sell order
                # order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                if current_price > limit_profit:
                    print("sold at win")
                    logger.info(f"sold at {current_price} with profit") 
                    order_succeeded = True

                if current_price < limit_lost:
                    print("sold at loss")
                    logger.info(f"sold at {current_price} with loss") 
                    order_succeeded = True

                if order_succeeded:
                    has_position = False
                else:
                    print("didn't sell")


            #reduce list to max 150 items to not get unlimited list
            closes = closes[-150:]
            highs = highs[-150:]
            lows = lows[-150:]
            volumes = volumes[-150:]
            # print("lengte: ", len(closes)) #check of de lengte wel 150 is



# pass a list of stream names
bm = BinanceSocketManager(client)
conn_key = bm.start_kline_socket(symbol="LITUSDT", callback=process_message, interval=KLINE_INTERVAL_1MINUTE)
# conn_key = bm.start_kline_socket(symbol="DOGEUSDT", callback=process_message, interval=KLINE_INTERVAL_1MINUTE)

bm.start() #start the socket manager
