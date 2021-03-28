
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
import numpy as np
import logging 
import math
#region variables
API_KEY = "SZLgVpzpnAoroc2YTSJ3hVJmBIH4tANSBO5I0dobNw4ORbFdysAoJVP0tR9pE9CF" 
SECRET_KEY = "YHyoGrthBZoqg0gEcVuvwkuRul7L4NxcqjaxHXDM0cbVjRPkN6S7eQCzyeywfVgu"
client = Client(API_KEY, SECRET_KEY)

symbol_info = client.get_symbol_info("LITUSDT")
for f in symbol_info['filters']:
    if f['filterType'] == 'LOT_SIZE':
        step_size = float(f['stepSize'])
        precision = int(round(-math.log(step_size, 10), 0))
        # print(name, " precision: ",globals()[name].precision)
        print(precision)



def get_amount(number:float, decimals:int=2):
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor


asset = client.get_isolated_margin_account(symbols="LITUSDT")
tradeable_amount = get_amount(float(asset["assets"][0]["baseAsset"]["free"]), precision)
print(tradeable_amount)

print(asset["assets"][0]["baseAsset"]["free"])