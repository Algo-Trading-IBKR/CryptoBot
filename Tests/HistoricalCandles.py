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


closes = []


client = Client(API_KEY, SECRET_KEY)
klines = client.get_historical_klines("BNBUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
# print(klines[-1][4]) #last close of last candle
print(len(closes))

for kline in klines:
    # print("kline: ", kline)
    closes.append(float(kline[4]))

print(len(closes))


# test webhook

np_closes = np.array(closes)
rsi = talib.RSI(np_closes, timeperiod=11)
last_rsi = rsi[-1]
print("latest rsi: ", last_rsi)
current_price = np_closes[-1]
previous = np_closes[-2]
print(current_price, previous)
