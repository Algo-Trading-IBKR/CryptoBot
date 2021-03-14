
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
print(info["assets"][0]["baseAsset"])
print(info["assets"][0]["quoteAsset"])
print(info["assets"][0]["liquidatePrice"])
print(info["assets"][0]["marginRatio"])




balance = client.get_asset_balance(asset='USDT')
# info = client.get_margin_account()
# info = client.get_isolated_margin_account()

amount = 1.0989
can_sell = amount - (amount * 0.002) 



symbol_info = client.get_symbol_info('DOGEUSDT')
step_size = 0.0
for f in symbol_info['filters']:
  if f['filterType'] == 'LOT_SIZE':
    step_size = float(f['stepSize'])


precision = int(round(-math.log(step_size, 10), 0))
quantity = float(round(1.0989, 3))
print("precision: ",precision)
# info = client.get_exchange_info() 
# print(balance)
print("quantity: ", quantity)