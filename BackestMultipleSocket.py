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



# rsi
rsi_period = 14
rsi_overbought = 80
rsi_oversold = 20

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12

# others, to be changed
highs = []
lows = []
volumes = []
closes = []
limit_lost = 1000
limit_profit = 0
has_position = False
stop_loss = 2
take_profit = 3
money = 100
#endregion
tickers = ["BNBUSDT", "DOGEUSDT"]


client = Client(API_KEY, SECRET_KEY)


if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, status server: ", status["msg"])
    



def process_message(msg):
    check_change(msg['s']) #ticker
    candle = msg['k']
    candle_closed = candle['x']
    
    if candle_closed:
        print("message: ", msg)
        

    
def check_change(ticker):
    print(ticker)

def make_list(ticker):
    print(ticker)



#create the websockets
bm = BinanceSocketManager(client, user_timeout=60)

for ticker in tickers:
    make_list(ticker)
    conn_key = bm.start_kline_socket(symbol=ticker, callback=process_message, interval=KLINE_INTERVAL_1MINUTE)

bm.start() #start the socket manager
