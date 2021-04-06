
import time
import pandas as pd
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

money = 100

pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT","CAKEUSDT","REEFUSDT", "TROYUSDT", "DODOUSDT" ,"ENJUSDT", "VTHOUSDT","AXSUSDT","CRVUSDT","UNFIUSDT"]

# make margin accounts (isolated)
# for p in pairs:
#     p = p[:-4]
#     try:
#         account = client.create_isolated_margin_account(base=p, quote='USDT')
#         print(account)
#     except Exception as e:
#         print(e)
    
    # print(p)




info = client.get_isolated_margin_account(symbols="LITUSDT")
# x =  json.loads(info)
# print(info["assets"][0]["baseAsset"])
# print(info["assets"][0]["quoteAsset"])
# print(info["assets"][0]["liquidatePrice"])
# print(info["assets"][0]["marginRatio"])




balance = client.get_asset_balance(asset='USDT')
info = client.get_margin_account()
info = client.get_isolated_margin_account()

# amount = 1.2879
# can_sell = amount - (amount * 0.002) 




# step_size = 0.0
# pairs = ["FTMUSDT"]
# for p in pairs:
#   symbol_info = client.get_symbol_info(p)
#   print(symbol_info)
#   for f in symbol_info['filters']:
#     if f['filterType'] == 'LOT_SIZE':
#       step_size = float(f['stepSize'])
#       precision = int(round(-math.log(step_size, 10), 0))
      
#       print(p, " precision: ",precision, type(precision))
#     elif f['filterType'] == "PRICE_FILTER":
#       minPrice = float(f['minPrice'])
#       precision = int(round(-math.log(minPrice, 10), 0))
      
#       print(p, " precision price: ",precision, type(precision))

# precision = 2
# quantity = float(round(amount, precision))

# print(quantity)



def get_amount(number:float, decimals:int=2, floor:bool=True):
# https://kodify.net/python/math/round-decimals/#round-decimal-places-down-in-python
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    if floor:
          return math.floor(number * factor) / factor
    elif floor == False:
        return math.ceil(number * factor) / factor
          
      


test = get_amount(0.45854*1.011, 5)
print(test)
# test = get_amount(number=amount*10, decimals=precision)
# print(test)
# info = client.get_exchange_info() 
# print(balance)
# print("quantity: ", quantity)