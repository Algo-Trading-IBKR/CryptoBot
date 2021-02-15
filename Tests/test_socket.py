import time
import pandas as pd
from binance.client import Client
import socket

# from binance.websockets import BinanceSocketManager
# from binance.enums import *
import json


API_KEY = "hKclENu75kFYky6xVXxHqVNzdzOQc0RAZ5kElzJggmF3N2EQDn4XjP2XPhHtbxjI"
SECRET_KEY = "2albG5h0FVjUpvIjg1aQvoVXH6sDgUvWsMmyzkajjaPkIrHaKUYUVgvraC86a7iS"


client = Client(API_KEY, SECRET_KEY)
# bm = BinanceSocketManager(client, user_timeout=60)


if str(client.ping()) == '{}':
    conn_key = bm.start_kline_socket('BNBBTC', process_message)


def process_message(msg):
    print("message type: {}".format(msg['e']))
    print(msg)
