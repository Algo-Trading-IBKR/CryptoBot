#region imports
# from Classes.ticker import Ticker
from twisted.internet import reactor

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

API_KEY = "mUjaGpF3VpQdNrGt49rEnQ0ba9teF8OMPlUVFEL4ByDaEMcNjUw0zaWcHoVlOF2a "
SECRET_KEY = "N4eMqt2PBbCugv3qNT9iDYJEBGcZBAZJo9PI1CBhYXZMRoYoJgXZHnDZupCJMIly"
# Testnet keys
API_KEY_TESTNET = "hmuUZY958uABtMw2JVYI88Dc1CEPIo589bvCTPs6ZEGevQ6Nd7ARzsCdXcapiKof"
SECRET_KEY_TESTNET = "8l1P0MyhNKw8P4Xanr7zTrojFhBTFAoBTKFW5DiUil78kh7zRXtztilje5jQ6RYT"
# rsi
rsi_period = 14
rsi_overbought = 80
rsi_oversold = 19

# mfi
mfi_period = 12
mfi_overbought = 80
mfi_oversold = 12


#endregion




from binance.enums import *
client = Client(API_KEY, SECRET_KEY)

order = client.create_order(
    symbol='DOGEUSDT',
    side=SIDE_BUY,
    type=ORDER_TYPE_LIMIT,
    timeInForce=TIME_IN_FORCE_IOC,
    quantity=200,
    price='0.0539')

info = client.get_symbol_info('DOGEUSDT')

print(info['filters'][2]['minQty'])
