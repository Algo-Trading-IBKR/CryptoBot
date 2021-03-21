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
import math
import sys,os
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
# x = list for websocket | y = make isolated wallet accounts 
for p in pairs:
    x = p.lower() + '@kline_1m' # dotusdt@kline_1m
    y = p[:-4]
    try:
        account = client.create_isolated_margin_account(base=y, quote='USDT')
    except Exception as e:
        print(e)     
    tickers.append(x)

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
        # get precision
        symbol_info = client.get_symbol_info(name)
        for f in symbol_info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                globals()[name].precision = int(round(-math.log(step_size, 10), 0))
                # print(name, " precision: ",globals()[name].precision)
         

        # Database.update_ticker(ticker=name, datetime=dt.datetime.now(),shares=0.0, averagePrice=0.0, realizedpnl=0.0)
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
    return total_money

# orders
# side effect: AUTO_REPAY, MARGIN_BUY
def send_order(side, quantity, ticker, price, order_type, isolated, side_effect):
    try:
        print("Sending order...")
        # print("limit order")
        order = client.create_margin_order(side=side, quantity=quantity, symbol=ticker, price=price, type=order_type, isIsolated=isolated, sideEffectType=side_effect, timeInForce=TIME_IN_FORCE_FOK)
        if order["status"] == "FILLED":
            return True
        else:
            return False
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

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

def process_m_message(msg):
    global total_money
    try:        
        if msg['data']['e'] == 'error':
            print("error while restarting socket")
        else:
            name = msg['data']['s']
            symbol = globals()[name]

            candle = msg['data']['k']
            candle_closed = candle['x']
            close = candle['c']
            high = candle['h']
            low = candle['l']
            volume = candle['v']

            if candle_closed:
                symbol.closes.append(float(close))
                symbol.highs.append(float(high))
                symbol.lows.append(float(low))
                symbol.volumes.append(float(volume))
                if len(symbol.closes) > 149:
                    rsi = talib.RSI(np.array(symbol.closes), timeperiod=rsi_period)
                    mfi = talib.MFI(np.array(symbol.highs), np.array(symbol.lows), np.array(symbol.closes), np.array(symbol.volumes), timeperiod=mfi_period)
                    last_rsi = rsi[-1]
                    last_mfi = mfi[-1]

                    # # verkopen
                    # if symbol.has_position:
                    #     current_price = symbol.closes[-1]
                    #     current_high = symbol.highs[-1]
                    #     order_succeeded = False

                    #     # sell with a profit
                    #     if current_high > float(symbol.take_profit):
                    #         print(Fore.RED + f"{name} sold with a profit.")
                    #         symbol.money += symbol.amount * symbol.take_profit
                    #         try:
                    #             response = clickatell.sendMessage(to=phone_numbers, message=f"{name} sold with a profit. money left: {symbol.money}.")
                    #         except Exception as e:
                    #             pass
                    #         symbol.log_sell(profit=True ,price=symbol.take_profit ,ticker=name ,amount=symbol.amount ,money=symbol.money)
                    #         order_succeeded = True
                    #         symbol.amount = 0
                    #         if order_succeeded:
                    #             symbol.has_position = False
                    #             order_succeeded = False

                        
                    #     # sell with a loss of initiate piramiding
                    #     if current_price < float(symbol.stop_loss):
                    #         # piramidding
                    #         if float(symbol.money) > 20:
                    #             print(Fore.RED  +f"{name} price dropped under the stop loss, buy a second time.")
                    #             piramidding_amount = symbol.money/current_price
                    #             symbol.average_price = (symbol.amount*symbol.average_price + piramidding_amount*current_price) / (symbol.amount+piramidding_amount)
                    #             symbol.log_buy(amount=piramidding_amount ,buy_price=current_price, ticker=name, money=symbol.money)
                    #             symbol.amount += piramidding_amount
                    #             symbol.stop_loss = get_low(symbol.ticker)
                    #             if float(symbol.stop_loss) > (symbol.average_price - (symbol.average_price*0.05)):
                    #                 symbol.stop_loss = symbol.average_price - (symbol.average_price*0.05)
                    #             symbol.take_profit = symbol.average_price * 1.012
                    #             symbol.money -= current_price * piramidding_amount
                    #             order_succeeded = True

                    #             if order_succeeded:
                    #                 print(Fore.GREEN + f"SECOND BUY: {name} bought for {current_price} dollar. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                    #                 try:
                    #                     response = clickatell.sendMessage(to=phone_numbers, message=f"SECOND BUY: {name} bought for {current_price} dollar.")
                    #                 except Exception as e:
                    #                     pass
                    #                 symbol.has_position = True
                    #                 order_succeeded = False

                    #         # loss
                    #         else:
                    #             print(Fore.RED  +f"{name} sold with a loss.")
                    #             symbol.money += symbol.amount * current_price
                    #             try:
                    #                 response = clickatell.sendMessage(to=phone_numbers, message=f"{name} sold with a loss. money left: {symbol.money}.")
                    #             except Exception as e:
                    #                 pass
                    #             symbol.log_sell(profit=False ,price=current_price ,ticker=name ,amount=symbol.amount ,money=symbol.money)
                    #             order_succeeded = True
                    #             symbol.amount = 0
                    #             if order_succeeded:
                    #                 symbol.has_position = False
                    #                 order_succeeded = False
 
                    # kopen
                    if last_rsi < rsi_oversold and last_mfi < mfi_oversold and total_money >= 22:
                        if symbol.has_position:
                            print(f"You already own {name}.")

                        else:
                            symbol.average_price = symbol.closes[-1] #get the wanted buy price
                            symbol.amount = (22/2)/symbol.average_price #get amount the bot could buy

                            # symbol.stop_loss = get_low(symbol.ticker) #get a stop loss
                            # if float(symbol.stop_loss) > (symbol.average_price - (symbol.average_price*0.03)):
                            #     symbol.stop_loss = symbol.average_price - (symbol.average_price*0.03)

                            symbol.take_profit = symbol.average_price * 1.011 #get a take profit amount

                            # limit order: check if filled
                            limit_buy = send_order(side=SIDE_BUY , quantity=symbol.amount, ticker=symbol,price=10,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY")
                            print(limit_buy)

                            if order_succeeded:
                                # log buy 
                                
                                symbol.log_buy(amount=symbol.amount ,buy_price=symbol.average_price, ticker=name, money=symbol.money)
                                print(Fore.GREEN + f"{name} bought for {symbol.average_price} dollar. rsi: {last_rsi} mfi: {last_mfi}. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                                try:
                                    response = clickatell.sendMessage(to=phone_numbers, message=f"{name} bought for {symbol.average_price} dollar.")
                                except Exception as e:
                                    pass
                                symbol.has_position = True
                                order_succeeded = False
                #  total money ophalen elke minuut
                total_money = get_money()

                symbol.closes = symbol.closes[-150:]
                symbol.highs = symbol.highs[-150:]
                symbol.lows = symbol.lows[-150:]
                symbol.volumes = symbol.volumes[-150:]

    except Exception as e:
        now = dt.datetime.now()
        date = now.strftime("%d/%m/%Y")
        hour = now.strftime("%H:%M:%S")

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        file = open(error_log_file,"a")
        file.write(f'\n{date}\n{hour}\nan error occured: {e}\n{exc_type}\n{fname}\nLine: {exc_tb.tb_lineno}\n')
        file.close()

        Database.insert_error_log(now, f"{e}\n{exc_type}", fname, f"{exc_tb.tb_lineno}")
        raise e

            








# initialize the socket when there is a connection
if str(client.ping()) == '{}':
    conn_key = bm.start_multiplex_socket(tickers, process_m_message)
    bm.start() #start the socket manager


# https://python-binance.readthedocs.io/en/latest/margin.html#orders
# when buy order is received -> send money to margin (Isolated if cross is not available)
# when sold -> transfer isolated margin back to spot wallet

# make sure time is synced in the beginning (look how to on pi)
