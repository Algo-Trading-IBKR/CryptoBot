#region imports
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json


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


closes = []
has_position = False
#endregion

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
    # print("message type: {}".format(msg['e']))
    print("message received")
    # print(msg)

    candle = msg['k']
    candle_closed = candle['x']
    close = candle['c']

    if candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("closes")


    # do something

def process_m_message(msg):
    global closes
    print("msg: ",msg)
    candle = msg['data']['k']
    candle_closed = candle['x']
    close = candle['c']
    # print("stream: {} data: {}".format(msg['stream'], msg['data']))
    if candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print(closes)

# pass a list of stream names
bm = BinanceSocketManager(client, user_timeout=60)
conn_key = bm.start_multiplex_socket(['bnbbtc@kline_1m', 'neobtc@kline_1m'], process_m_message)

bm.start() #start the socket manager
