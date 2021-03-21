#region imports
# own classes
# from Classes.ticker import Ticker
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
from tqdm import tqdm
from colorama import Fore, Back, Style,init
import datetime as dt
init(autoreset=True)
#endregion

#region variables - To be converted to Config file

API_KEY = "01rU5GpozT4Owzs0MJNqSIO9KloKJERtpJscOs1gC7gYkcSTWdry4KJYMTl1Sxu4"
SECRET_KEY = "mzYubBy1mRUVElxg2xP4lNAZW76BFDKRxkpDAUJK86pio8FHAxMVxDCCM5AgFPs6"

phone_numbers = ["32470579542","32476067619"]

clickatell = Rest("VmGMIQOQRryF3X8Yg-iUZw==")

# rsi
rsi_period = 14
rsi_overbought = 84
rsi_oversold = 19

# mfi
mfi_period = 12
mfi_overbought = 88
mfi_oversold = 12

# tickers
pairs = ["BTCUSDT", "ETHUSDT", "DOTUSDT", "ADAUSDT", "SFPUSDT","FTMUSDT","XEMUSDT","NPXSUSDT","KSMUSDT","ONTUSDT","RLCUSDT","ONGUSDT","OMGUSDT","MANAUSDT","XRPUSDT","BNBUSDT","CAKEUSDT","REEFUSDT", "TROYUSDT", "DODOUSDT" ,"ENJUSDT", "VTHOUSDT","AXSUSDT","CRVUSDT","UNFIUSDT"]
log_file = "./StrategyTests/OnePercentStopLossPiramiddingV4"
ErrorLogFile = "Errors.txt"
#endregion