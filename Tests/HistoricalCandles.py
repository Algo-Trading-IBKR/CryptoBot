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
klines = client.get_historical_klines("BNBUSDT", interval=Client.KLINE_INTERVAL_1MINUTE, start_str="1 day ago UTC")



