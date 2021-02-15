#region imports
import time, talib
import pandas as pd
import config
from binance.client import Client
from binance.websockets import BinanceSocketManager
from binance.enums import *
import json
import numpy as np
# 32.32
listTest = [135.508, 134.9999, 135.1071, 135.0954, 135.3511, 135.3296, 135.1851, 135.1529, 135.0509, 135.0476, 134.9074, 134.95, 135.0, 135.1832, 135.2442, 135.0295, 134.8988, 134.8671, 134.8108]
listTest2 = [135.508, 134.9999, 135.1071, 135.0954, 135.3511, 135.3296, 135.1851, 135.1529, 135.0509, 135.0476, 134.9074, 134.95, 135.0, 135.1832, 135.2442, 135.0295, 134.8988, 134.8671, 134.8108]
listTest2 = listTest2[-19:]
listTest3 = [135.1529,135.0509, 135.0476, 134.9074, 134.95, 135, 135.1832, 135.2442, 135.0295, 134.8988, 134.8671, 134.8108]
print(listTest3)

np_closes = np.array(listTest2)
rsi = talib.RSI(np_closes, timeperiod=11)
last_rsi = rsi[-1]
print(len(listTest2))
print("latest rsi: ", last_rsi)
# print(rsi)










