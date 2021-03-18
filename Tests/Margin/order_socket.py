import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
import numpy as np
import logging 

#region variables
API_KEY = "SZLgVpzpnAoroc2YTSJ3hVJmBIH4tANSBO5I0dobNw4ORbFdysAoJVP0tR9pE9CF" 
SECRET_KEY = "YHyoGrthBZoqg0gEcVuvwkuRul7L4NxcqjaxHXDM0cbVjRPkN6S7eQCzyeywfVgu"
client = Client(API_KEY, SECRET_KEY)
symbol = 'LITUSDT'

client = Client(API_KEY, SECRET_KEY)
bm = BinanceSocketManager(client, user_timeout=600)

def process_message(msg):
    print(msg)







if str(client.ping()) == '{}':
    conn_key = bm.start_isolated_margin_socket(symbol, process_message)
    bm.start()
