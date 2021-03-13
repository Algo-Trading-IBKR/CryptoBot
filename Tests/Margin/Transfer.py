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
data = client.get_asset_balance(asset='USDT')
total_money = data["free"]
print(f"you have {(float(total_money))} dollar of buying power in your spot wallet.")
details = client.get_max_margin_transfer(asset='USDT', isolatedSymbol=symbol)
print("max transfer back?" ,details)

# transfer money to isolated
if float(total_money) != 0: 
    transaction = client.transfer_spot_to_isolated_margin(asset='USDT',symbol='LITUSDT', amount=total_money)
    print(transaction)
# # transfer the money back
# transaction = client.transfer_isolated_margin_to_spot(asset='USDT',symbol='LITUSDT', amount='1.1')

print(f"you have {(float(total_money))} dollar of buying power in your spot wallet.")
details = client.get_max_margin_transfer(asset='USDT', isolatedSymbol=symbol)
print("max transfer back?" ,details)




# info = client.get_isolated_margin_account(symbols="LITUSDT")
# print(info)
# print(info["assets"][0]["baseAsset"])
# print(info["assets"][0]["quoteAsset"])
# print(info["assets"][0]["liquidatePrice"])
# print(info["assets"][0]["marginRatio"])


