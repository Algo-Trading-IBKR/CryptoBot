
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
API_KEY = "01rU5GpozT4Owzs0MJNqSIO9KloKJERtpJscOs1gC7gYkcSTWdry4KJYMTl1Sxu4"
SECRET_KEY = "mzYubBy1mRUVElxg2xP4lNAZW76BFDKRxkpDAUJK86pio8FHAxMVxDCCM5AgFPs6"
client = Client(API_KEY, SECRET_KEY)

balance = client.get_asset_balance(asset='USDT')
details = client.get_max_margin_loan(asset='BTC')

# info = client.get_exchange_info()
print(balance)
print(details)