
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


pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT","CAKEUSDT","REEFUSDT", "TROYUSDT", "DODOUSDT" ,"ENJUSDT", "VTHOUSDT","AXSUSDT","CRVUSDT","UNFIUSDT"]

# make margin accounts (isolated)
for p in pairs:
    p = p[:-4]
    try:
        account = client.create_isolated_margin_account(base=p, quote='USDT')
        print(account)
    except Exception as e:
        print(e)
    
    # print(p)






balance = client.get_asset_balance(asset='USDT')
info = client.get_margin_account()
info = client.get_isolated_margin_account()


# info = client.get_exchange_info() 
# print(balance)
# print(info)