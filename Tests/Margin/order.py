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

# orders
# side=SIDE_BUY
def send_order(side, quantity, ticker, price, order_type, isolated):
    try:
        print("Sending order...")
        if order_type == ORDER_TYPE_MARKET:
            print("market order")
            order = client.create_margin_order(symbol=ticker,side=side,type=order_type,quantity=quantity,isIsolated=isolated)
            print(order)

        if order_type == ORDER_TYPE_LIMIT:
            print("limit order")
            order = client.create_margin_order(symbol=ticker,side=side,type=order_type,timeInForce=TIME_IN_FORCE_FOK,quantity=quantity,price=price,isIsolated=isolated)
            print(order)

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True





test = send_order(side=SIDE_SELL , quantity=1.09, ticker=symbol,price=0,order_type=ORDER_TYPE_MARKET,isolated=True)
# print(test)