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
symbol = 'FTMUSDT'

# orders
# side=SIDE_BUY
def send_order(side, quantity, ticker, price, order_type, isolated,side_effect):
    try:
        print("Sending order...")
        if order_type == ORDER_TYPE_MARKET:
            print("market order")
            order = client.create_margin_order(symbol=ticker,side=side,type=order_type,quantity=quantity,isIsolated=isolated, sideEffectType=side_effect)
            print(order)

        if order_type == ORDER_TYPE_LIMIT:
            print("limit order")
            # order = client.create_margin_order(symbol=ticker,side=side,type=order_type,timeInForce=TIME_IN_FORCE_FOK,quantity=quantity,price=price,isIsolated=isolated,sideEffectType=side_effect,stopPrice=stopPrice)
            order = client.create_margin_order(symbol=ticker,side=side,type=order_type,timeInForce=TIME_IN_FORCE_GTC,quantity=quantity,price=price,isIsolated=isolated,sideEffectType=side_effect)
            print(order)
        



    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

 
# market_buy = send_order(side=SIDE_BUY , quantity=2, ticker=symbol,price=10,order_type=ORDER_TYPE_MARKET,isolated=True,side_effect="MARGIN_BUY")
# print(market_buy)

# market_sell = send_order(side=SIDE_SELL , quantity=2, ticker=symbol,price=10,order_type=ORDER_TYPE_MARKET,isolated=True,side_effect="AUTO_REPAY") 
# print(market_sell)

limit_buy = send_order(side=SIDE_BUY , quantity=9, ticker="SFPUSDT",price=3.1,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY") 
print(limit_buy)

# limit_sell = send_order(side=SIDE_SELL , quantity=120.8, ticker=symbol,price=0.45959,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="AUTO_REPAY")
# print(limit_sell)




# orders = client.get_all_margin_orders(symbol='LITUSDT',isIsolated=True)
# print(orders)
# orders = client.get_open_margin_orders(symbol='LITUSDT',isIsolated=True)
# print(orders)
# orders = client.get_all_margin_orders(symbol='LITUSDT', limit=4,isIsolated=True)

# trades = client.get_margin_trades(symbol='LITUSDT',limit=2,isIsolated=True)
# print(trades)



# transaction = client.repay_margin_loan(asset='USDT', amount='20.00125')
