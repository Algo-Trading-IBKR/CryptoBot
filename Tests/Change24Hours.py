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

client = Client(API_KEY, SECRET_KEY)



ticker = client.get_ticker(symbol='BNBUSDT')
change = ticker["priceChangePercent"]


status = client.get_account_status()
# avg_price = client.get_avg_price(symbol='BNBBTC')
details = client.get_asset_details()
balance = client.get_asset_balance(asset='BNBUSDT')
accounts = client.get_sub_account_list()
info = client.get_account()
print(info)