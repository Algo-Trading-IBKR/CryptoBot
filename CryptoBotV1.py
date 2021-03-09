#region imports
# own classes
from Classes.ticker import Ticker
from Classes.DatabaseRepository import Database 
# sms
from clickatell.rest import Rest
# strategy
import time, talib
import pandas as pd
import numpy as np
import json
# binance
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
# extra
import json
import datetime as dt
from tqdm import tqdm
from colorama import Fore, Back, Style,init
init(autoreset=True)
# config file
import configparser
config = configparser.ConfigParser()
config.read('./Configs/CryptoBot.ini')
#endregion

#region variables
clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==")

API = config['API']
NOTIFICATIONS = config['NOTIFICATIONS']
TICKERS = config['TICKERS']
RSI = config['RSI']
MFI = config['MFI']
LOGGING = config['LOGGING']

API_KEY = str(API['API_KEY'])
SECRET_KEY = str(API['SECRET_KEY'])

phone_numbers = json.loads(config.get("NOTIFICATIONS","phone_numbers"))

# rsi
rsi_period = int(RSI['rsi_period'])
rsi_overbought = int(RSI['rsi_overbought'])
rsi_oversold = int(RSI['rsi_oversold'])

# mfi
mfi_period = int(MFI['mfi_period'])
mfi_overbought = int(MFI['mfi_overbought'])
mfi_oversold = int(MFI['mfi_oversold'])

# tickers
pairs = json.loads(config.get("TICKERS","pairs"))

# logging
log_file = str(LOGGING['log_file'])
error_log_file = str(LOGGING['ErrorLogFile'])
#endregion

# region initialize
client = Client(API_KEY, SECRET_KEY)
bm = BinanceSocketManager(client, user_timeout=600)

tickers = []
for p in pairs:
    p = p.lower() + '@kline_1m' # dotusdt@kline_1m
    tickers.append(p)

if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, server status:", status["msg"])
    print("Fetching historical data.")
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]
    instances = []
    for x in tqdm(range(len(tickers))):
        name = tickers[x][:-9].upper()
        globals()[name] = Ticker(name, log_file)
        instances.append(globals()[name]) 
        klines = client.get_historical_klines(name.upper(), interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
        for k in klines:
            globals()[name].closes.append(float(k[4]))
            globals()[name].highs.append(float(k[2]))
            globals()[name].lows.append(float(k[3]))
            globals()[name].volumes.append(float(k[5]))
        Database.update_ticker(ticker=name, datetime=dt.datetime.now(),shares=0.0, averagePrice=0.0, realizedpnl=0.0)
    print(f"Data fetched, you have {(float(total_money)):.2f} dollar of buying power in your spot wallet.")

# endregion
# region functions
def get_low(ticker):
    data = client.get_ticker(symbol=ticker)
    low = data["lowPrice"]
    return low

def get_money():
    global total_money
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]

# orders
def send_order(side, quantity, ticker, price, order_type):
    try:
        print("Sending order...")
        order = client.create_margin_order(symbol=ticker,side=side,type=order_type,timeInForce=TIME_IN_FORCE_IOC,quantity=quantity,price=price)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

def cancel_order(ticker,order_id):
    try:
        print("Cancelling order...")
        result = client.cancel_margin_order(symbol=ticker,orderId=order_id)        
        print(result)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True



# endregion



# https://python-binance.readthedocs.io/en/latest/margin.html#orders
# when buy order is received -> send money to margin (Isolated if cross is not available)
# when sold -> transfer isolated margin back to spot wallet

