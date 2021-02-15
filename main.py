#region imports
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
import numpy as np

#endregion
#region variables
API_KEY = "hKclENu75kFYky6xVXxHqVNzdzOQc0RAZ5kElzJggmF3N2EQDn4XjP2XPhHtbxjI"
SECRET_KEY = "2albG5h0FVjUpvIjg1aQvoVXH6sDgUvWsMmyzkajjaPkIrHaKUYUVgvraC86a7iS"

# Testnet keys
API_KEY_TESTNET = "hmuUZY958uABtMw2JVYI88Dc1CEPIo589bvCTPs6ZEGevQ6Nd7ARzsCdXcapiKof"
SECRET_KEY_TESTNET = "8l1P0MyhNKw8P4Xanr7zTrojFhBTFAoBTKFW5DiUil78kh7zRXtztilje5jQ6RYT"

#indicator vars
TRADE_SYMBOL = 'BNBUSDT'
TRADE_QUANTITY = 15

# rsi
rsi_period = 11
rsi_overbought = 80
rsi_oversold = 20

closes = []
has_position = False
#endregion

# client aanmaken
client = Client(API_KEY, SECRET_KEY)


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
    bnb = client.get_asset_balance(asset='BNB')
    # trades = client.get_my_trades(symbol='BNBUSDT')
    print(f"Je hebt {balance['free']} USDT en {bnb['free']} BNB")
    print("data ophalen")
    klines = client.get_historical_klines("BNBUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
    for kline in klines:
        closes.append(float(kline[4]))
    print("data opgehaald")

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
    global closes
    candle = msg['k']
    candle_closed = candle['x']
    close = candle['c']
    symbol = msg['s']
    
    if candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))

        if len(closes) > rsi_period:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, rsi_period)
            macd, macdsignal, macdhist = talib.MACD(np_closes, fastperiod=12, slowperiod=26, signalperiod=9)
            last_macdhist = macdhist[-1]
            last_rsi = rsi[-1]
            print(f'macdhist: {last_macdhist}, rsi: {last_rsi}.')
            
            # KOPEN
            if last_rsi< rsi_oversold:
                if has_position:
                    print("It is oversold, but you already own it, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    #Binance buy order
                    # order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    order_succeeded = True
                    if order_succeeded:
                        has_position = True
            
            # VERKOPEN
            if last_rsi > rsi_overbought:
                if has_position:
                    print("Overbought! Sell! Sell! Sell!")
                    #binance sell order
                    # order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    order_succeeded = True
                if order_succeeded:
                        has_position = False
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")


            #reduce list to max 150 items to not get unlimited list
            closes = closes[-150:]
            # print("lengte: ", len(closes))








# pass a list of stream names
bm = BinanceSocketManager(client)
conn_key = bm.start_kline_socket(symbol="BNBUSDT", callback=process_message, interval=KLINE_INTERVAL_1MINUTE)
# conn_key = bm.start_kline_socket(symbol="DOGEUSDT", callback=process_message, interval=KLINE_INTERVAL_1MINUTE)

bm.start() #start the socket manager
