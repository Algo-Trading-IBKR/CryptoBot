

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
import math
import sys,os
import json
import datetime as dt

API_KEY = "SZLgVpzpnAoroc2YTSJ3hVJmBIH4tANSBO5I0dobNw4ORbFdysAoJVP0tR9pE9CF"
SECRET_KEY = "YHyoGrthBZoqg0gEcVuvwkuRul7L4NxcqjaxHXDM0cbVjRPkN6S7eQCzyeywfVgu"

client = Client(API_KEY, SECRET_KEY)


asset = client.get_isolated_margin_account(symbols="UNFIUSDT")
free_asset, borrowed_asset = float(asset["assets"][0]["baseAsset"]["free"]), float(asset["assets"][0]["baseAsset"]["borrowed"])
free_quote, borrowed_quote = float(asset["assets"][0]["quoteAsset"]["free"]), float(asset["assets"][0]["quoteAsset"]["borrowed"])
print("free_asset: <",free_asset, "> borrowed_asset: <",borrowed_asset, "> free_quote: <",free_quote, "> borrowed_quote: <",borrowed_quote,">")

transaction = client.repay_margin_loan(asset='USDT', amount=borrowed_quote, isIsolated='TRUE', symbol="UNFIUSDT")
print(transaction)