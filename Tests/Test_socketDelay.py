#region imports
from Classes.ticker import Ticker
from twisted.internet import reactor

from clickatell.rest import Rest
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
from tqdm import tqdm
import numpy as np
from colorama import Fore, Back, Style,init
init(autoreset=True)

#endregion

#region variables

API_KEY = "01rU5GpozT4Owzs0MJNqSIO9KloKJERtpJscOs1gC7gYkcSTWdry4KJYMTl1Sxu4"
SECRET_KEY = "mzYubBy1mRUVElxg2xP4lNAZW76BFDKRxkpDAUJK86pio8FHAxMVxDCCM5AgFPs6"
# Testnet keys
API_KEY_TESTNET = "hmuUZY958uABtMw2JVYI88Dc1CEPIo589bvCTPs6ZEGevQ6Nd7ARzsCdXcapiKof"
SECRET_KEY_TESTNET = "8l1P0MyhNKw8P4Xanr7zTrojFhBTFAoBTKFW5DiUil78kh7zRXtztilje5jQ6RYT"

clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==");
# rsi
rsi_period = 14
rsi_overbought = 80
rsi_oversold = 19

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12


#endregion
# region initialize
client = Client(API_KEY, SECRET_KEY)
bm = BinanceSocketManager(client, user_timeout=30)

pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","SOLUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT"]
tickers = []
for p in pairs:
    p = p.lower() + '@kline_1m'
    tickers.append(p)
# print(tickers)
# tickers = ["btcusdt@kline_1m","ethusdt@kline_1m","dotusdt@kline_1m"]

if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected, server status:", status["msg"])
    print("Fetching data.")
    data = client.get_asset_balance(asset='USDT')
    total_money = data["free"]

    instances = []
    for x in tqdm(range(len(tickers))):
        name = tickers[x][:-9].upper()
        globals()[name] = Ticker(name)
        instances.append(globals()[name]) 
        uppercase_name = name.upper()
        klines = client.get_historical_klines(uppercase_name, interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
        
        for k in klines:
            globals()[name].closes.append(float(k[4]))
            globals()[name].highs.append(float(k[2]))
            globals()[name].lows.append(float(k[3]))
            globals()[name].volumes.append(float(k[5]))
    print(f"Data fetched, you have {total_money} dollar buying power in your spot wallet.")

# endregion
# region functions
def get_change(ticker):
    data = client.get_ticker(symbol=ticker)
    change = data["priceChangePercent"]
    # print(ticker, " change in price: ", change)
    return change

def get_low(ticker):
    data = client.get_ticker(symbol=ticker)
    low = data["lowPrice"]
    # print(ticker, " change in price: ", change)
    return low

# endregion


def process_m_message(msg):
    if msg['data']['e'] == 'error':
        print("error while restarting socket")
    else:
        candle = msg['data']['k']
        candle_closed = candle['x']
        name = msg['data']['s']
        symbol = globals()[name]
        if candle_closed:
            print(Fore.GREEN + symbol.ticker)
        


if str(client.ping()) == '{}':
    conn_key = bm.start_multiplex_socket(tickers, process_m_message)
    bm.start() #start the socket manager
