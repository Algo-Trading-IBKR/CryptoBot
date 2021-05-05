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
from decimal import Decimal
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

API = config['API_YENTE']
BUDGET = config['BUDGET_YENTE']

# API = config['API_JOREN']
# BUDGET = config['BUDGET_JOREN']

NOTIFICATIONS = config['NOTIFICATIONS']
TICKERS = config['TICKERS']
RSI = config['RSI']
MFI = config['MFI']
LOGGING = config['LOGGING']

API_KEY = str(API['API_KEY'])
SECRET_KEY = str(API['SECRET_KEY'])

phone_numbers = json.loads(config.get("NOTIFICATIONS","phone_numbers"))

#budgets
budget = float(BUDGET['budget'])
budget_divider = float(BUDGET['budget_divider'])
minimum_cash = float(BUDGET['minimum_cash'])

# rsi
rsi_period = int(RSI['rsi_period'])
rsi_overbought = int(RSI['rsi_overbought'])
rsi_oversold = int(RSI['rsi_oversold'])

# mfi
mfi_period = int(MFI['mfi_period'])
mfi_overbought = int(MFI['mfi_overbought'])
mfi_oversold = int(MFI['mfi_oversold'])

# tickers
pairs = json.loads(config.get("TICKERS","pairs_live"))

# logging
log_file = str(LOGGING['log_file'])
error_log_file = str(LOGGING['ErrorLogFile'])
#endregion

# region initialize
client = Client(API_KEY, SECRET_KEY)
bm = BinanceSocketManager(client, user_timeout=600)

tickers = []
isolated_accounts_failed = []
# x = list for websocket | y = make isolated wallet accounts
print("Creating isolated margin accounts.") 
for p in tqdm(pairs):
    x = p.lower() + '@kline_1m' # dotusdt@kline_1m
    y = p[:-4]
    try:
        account = client.create_isolated_margin_account(base=y, quote='USDT')
    except Exception as e:
        isolated_accounts_failed.append(p)
    tickers.append(x)

# print list of already existing isolated wallets
isolated_accounts_failed.append(" -> these isolated wallets already exists.")
print(*isolated_accounts_failed, sep = ", ")  

# endregion

# region functions
def get_low(ticker):
    data = client.get_ticker(symbol=ticker)
    low = float(data["lowPrice"])
    return low

def get_money():
    global total_money
    data = client.get_asset_balance(asset='USDT')
    total_money = float(data["free"])
    # print("total money:" ,total_money)

def get_amount(number:float, decimals:int=2, floor:bool=True):
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    if floor:
        return math.floor(number * factor) / factor
    elif floor == False:
        return math.ceil(number * factor) / factor
    

# orders
# side effect: AUTO_REPAY, MARGIN_BUY
def send_order(side, quantity, ticker, price, order_type, isolated, side_effect, timeInForce):
    symbol = globals()[ticker]
    global total_money
    try:
        print("Sending {side_effect} order for {ticker}")
        # print("limit order")
        order = client.create_margin_order(side=side, quantity=quantity, symbol=ticker, price=price, type=order_type, isIsolated=isolated, sideEffectType=side_effect, timeInForce=timeInForce)
        print(order)
        get_money()
        if order["side"] == "SELL":
            symbol.TP_order_ID = order['orderId'] #instantie
            return False
        if order["status"] == "FILLED" and order["side"] == "BUY":
            symbol.open_order = False
            return True
        elif order["side"] == "BUY":
            symbol.BUY_order_ID = order['orderId']
            symbol.open_order = True
            print("buyOrderID: {symbol.BUY_order_ID}")
            return False
    except Exception as e:
        now = dt.datetime.now()
        date = now.strftime("%d/%m/%Y")
        hour = now.strftime("%H:%M:%S")

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        file = open(error_log_file,"a")
        file.write(f'\n{date}\n{hour}\nan error occured: {e}\n{exc_type}\n{fname}\nLine: {exc_tb.tb_lineno}\n')
        file.close()
        print(str(e))

        #Database.insert_error_log(now, f"{e}\n{exc_type}", fname, f"{exc_tb.tb_lineno}")
        return False

def cancel_order(ticker, order_id):
    try:
        print(f"Cancelling order for {ticker}")
        result = client.cancel_margin_order(symbol=ticker,orderId=order_id,isIsolated="TRUE")        
        print(result)
    except Exception as e:
        now = dt.datetime.now()
        date = now.strftime("%d/%m/%Y")
        hour = now.strftime("%H:%M:%S")

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        file = open(error_log_file,"a")
        file.write(f'\n{date}\n{hour}\nan error occured: {e}\n{exc_type}\n{fname}\nLine: {exc_tb.tb_lineno}\n')
        file.close()
        print(str(e))

        #Database.insert_error_log(now, f"{e}\n{exc_type}", fname, f"{exc_tb.tb_lineno}")
        return False
    return True

# transfer
def transfer_to_isolated(asset, ticker, amount):
    global total_money
    t = client.transfer_spot_to_isolated_margin(asset=asset,symbol=ticker, amount=amount)
    get_money()
    return t

def transfer_to_spot(asset, ticker, amount):
    global total_money
    t = client.transfer_isolated_margin_to_spot(asset=asset,symbol=ticker, amount=amount)
    get_money()
    return t


# endregion

# region callbacks
def process_m_message(msg):
    try:        
        if msg['data']['e'] == 'error':
            print("error while restarting socket")
        else:
            name = msg['data']['s']
            symbol = globals()[name]

            candle = msg['data']['k']
            candle_closed = candle['x']
            close = float(candle['c'])
            high = float(candle['h'])
            low = float(candle['l'])
            volume = float(candle['v'])

            if candle_closed:
                symbol.closes.append(close)
                symbol.highs.append(high)
                symbol.lows.append(low)
                symbol.volumes.append(volume)
                if len(symbol.closes) > 149:
                    rsi = talib.RSI(np.array(symbol.closes), timeperiod=rsi_period)
                    mfi = talib.MFI(np.array(symbol.highs), np.array(symbol.lows), np.array(symbol.closes), np.array(symbol.volumes), timeperiod=mfi_period)
                    last_rsi = rsi[-1]
                    last_mfi = mfi[-1]

                    if symbol.open_order:
                        # plaats hier de cancel order
                        cancel = cancel_order(ticker=symbol.ticker,order_id=symbol.BUY_order_ID)
                        print(f"Na 1 minuut nog niet gekocht -> cancel: {cancel}")
                        symbol.open_order = False
                        asset = client.get_isolated_margin_account(symbols=name)
                        free_asset, borrowed_asset = float(asset["assets"][0]["baseAsset"]["free"]), float(asset["assets"][0]["baseAsset"]["borrowed"])
                        free_quote, borrowed_quote = float(asset["assets"][0]["quoteAsset"]["free"]), float(asset["assets"][0]["quoteAsset"]["borrowed"])
                        print(f"Cancel Order: free_asset {free_asset}  borrowed_asset {borrowed_asset},  free_quote {free_quote}, borrowed_quote {borrowed_quote}")  
                        transaction = client.repay_margin_loan(asset='USDT', amount=borrowed_quote, isIsolated='TRUE', symbol=name)
                        print("tussen de repay en transfer back voor de cancel")
                        if free_asset != 0:
                            transaction_asset = transfer_to_spot(asset=name[:-4], ticker=symbol.ticker, amount=free_asset) 
                            print("transaction_asset: {transaction_asset}")
                        print("______________________________________________________________________________________")
                        if free_quote != 0:
                            transaction_quote = transfer_to_spot(asset="USDT", ticker=symbol.ticker, amount=free_quote)
                            print("transaction_quote: {transaction_quote}")
                        symbol.has_position = False
                        symbol.piramidding = False

                    # verkopen
                    if symbol.has_position:
                        current_price = symbol.closes[-1]
                        current_high = symbol.highs[-1]
                        order_succeeded = False
                        get_money()

                        #initiate piramiding
                        if current_price < symbol.stop_loss and total_money >= budget and symbol.piramidding == False:
                            transaction = transfer_to_isolated(asset="USDT", ticker=symbol.ticker, amount=budget)
                            symbol.piramidding = True
                            asset = client.get_isolated_margin_account(symbols=name)
                            free_asset, borrowed_asset = float(asset["assets"][0]["baseAsset"]["free"]), float(asset["assets"][0]["baseAsset"]["borrowed"])
                            free_quote, borrowed_quote = float(asset["assets"][0]["quoteAsset"]["free"]), float(asset["assets"][0]["quoteAsset"]["borrowed"])
                            if free_quote >= budget:
                                print(f"PIRAMMIDING: free_asset {free_asset}  borrowed_asset {borrowed_asset},  free_quote {free_quote}, borrowed_quote {borrowed_quote}")  
                                print(Fore.RED  +f"{name} price dropped under the stop loss, buy a second time.")
                                cancel = cancel_order(ticker=symbol.ticker,order_id=symbol.TP_order_ID)
                                symbol.piramidding_amount = get_amount((budget)/current_price, symbol.precision)
                                symbol.buy_price= current_price
                                # take profit after average price
                                order_succeeded = send_order(side=SIDE_BUY , quantity=Decimal(symbol.piramidding_amount*symbol.margin_ratio), ticker=symbol.ticker,price=current_price,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY",timeInForce=TIME_IN_FORCE_GTC)
                                symbol.average_price_piramidding = (symbol.amount*symbol.average_price + symbol.piramidding_amount*current_price) / (symbol.amount+symbol.piramidding_amount)
                                symbol.take_profit = get_amount(symbol.average_price_piramidding * 1.012,symbol.precision_minPrice, False)
                                if order_succeeded:
                                    symbol.log_buy(amount=symbol.piramidding_amount ,buy_price=current_price, ticker=name, money=symbol.money)
                                    # get amount for limit sell order
                                    asset = client.get_isolated_margin_account(symbols=name)
                                    symbol.amount = get_amount(float(asset["assets"][0]["baseAsset"]["free"]), symbol.precision)
                                    take_profit_order = send_order(side=SIDE_SELL , quantity=Decimal(symbol.amount), ticker=symbol.ticker,price=symbol.take_profit,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="AUTO_REPAY",timeInForce=TIME_IN_FORCE_GTC)
                                    symbol.has_position = True
                                    order_succeeded = False
                                    print(Fore.GREEN + f"SECOND BUY: {name} bought for {current_price} dollar. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                            elif free_quote < budget:
                                print(f"PIRAMMIDING {symbol.ticker} Failed, Not enough money")
 
                    # kopen
                    if last_rsi < rsi_oversold and last_mfi < mfi_oversold and total_money >= budget+minimum_cash:
                        if symbol.has_position:
                            print(f"You already own {name}.")

                        else:
                            print("in the buy")
                            transaction = transfer_to_isolated(asset="USDT", ticker=symbol.ticker, amount=budget)
                            symbol.average_price = symbol.closes[-1] #get the wanted buy price 
                            symbol.amount = get_amount((budget/budget_divider)/symbol.average_price, symbol.precision) #get amount the bot could buy

                            symbol.stop_loss = get_low(symbol.ticker) #get a stop loss
                            if symbol.stop_loss > (symbol.average_price - (symbol.average_price*0.06)):
                                symbol.stop_loss = symbol.average_price - (symbol.average_price*0.06)
                            symbol.take_profit = get_amount(symbol.average_price * 1.012,symbol.precision_minPrice, False) #get a take profit amount
                            print(f"symbol.amount: {symbol.amount}")
                            print(f"symbol.margin_ratio: {symbol.margin_ratio}")

                            # print(f"symbol.amount: {type(symbol.amount)}")
                            # print(f"symbol.margin_ratio: {type(symbol.margin_ratio)}")
                            symbol.buy_price= symbol.average_price
                            time.sleep(0.1)
                            order_succeeded = send_order(side=SIDE_BUY , quantity=Decimal(symbol.amount*symbol.margin_ratio), ticker=symbol.ticker,price=symbol.average_price,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY",timeInForce=TIME_IN_FORCE_GTC)
                            print("order succeeded",order_succeeded)

                            if order_succeeded:
                                # log buy 
                                print('gekocht via direct FILL')
                                symbol.log_buy(amount=symbol.amount ,buy_price=symbol.average_price, ticker=name, money=symbol.money)
                                print(Fore.GREEN + f"{name} bought for {symbol.average_price} dollar. rsi: {last_rsi} mfi: {last_mfi}. pirammiding at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                                symbol.has_position = True
                                transaction = transfer_to_isolated(asset="USDT", ticker=symbol.ticker, amount=1)
                                order_succeeded = False

                                # get amount in wallet
                                asset = client.get_isolated_margin_account(symbols=name)
                                symbol.amount = get_amount(float(asset["assets"][0]["baseAsset"]["free"]), symbol.precision)
                                take_profit_order = send_order(side=SIDE_SELL , quantity=Decimal(symbol.amount), ticker=symbol.ticker,price=symbol.take_profit,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="AUTO_REPAY",timeInForce=TIME_IN_FORCE_GTC)
                                symbol.liquidation_price = float(asset["assets"][0]["liquidatePrice"])
                                if symbol.liquidation_price > symbol.stop_loss:
                                    symbol.stop_loss = symbol.liquidation_price *1.0075
                
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

        #Database.insert_error_log(now, f"{e}\n{exc_type}", fname, f"{exc_tb.tb_lineno}")
        raise e

            
def callback_isolated_accounts(msg):
    try:
        # sell function here https://binance-docs.github.io/apidocs/spot/en/#payload-balance-update
        # check if any are still borrowed
        print("total money: " ,total_money)
        # print(msg)
        event = msg['e']
        if event == "executionReport":
            name = msg['s']
            symbol = globals()[name]
            side = msg['S'] #BUY or SELL
            order_type = msg['o']
            execution_type = msg['x'] # is TRADE when order has been filled
            execution_status = msg['X']
            error = msg['r'] #is NONE when no issues
            TP_orderID = msg['i']
            # when the take profit order is reached
            if side == "SELL" and execution_type == "TRADE" and execution_status == "FILLED" and TP_orderID == symbol.TP_order_ID: 
                symbol.piramidding = False
                time.sleep(1)
                asset = client.get_isolated_margin_account(symbols=name)
                free_asset, borrowed_asset = float(asset["assets"][0]["baseAsset"]["free"]), float(asset["assets"][0]["baseAsset"]["borrowed"])
                free_quote, borrowed_quote = float(asset["assets"][0]["quoteAsset"]["free"]), float(asset["assets"][0]["quoteAsset"]["borrowed"])
                print(f"Sell: free_asset {free_asset}  borrowed_asset {borrowed_asset},  free_quote {free_quote}, borrowed_quote {borrowed_quote}")
                # print("test bij sell order filled -> volgende print -moet nothing borrowed- zijn")
                if borrowed_asset == 0 and borrowed_quote == 0: 
                    #transaction to spot
                    print("nothing borrowed: True")
                    transaction_asset = transfer_to_spot(asset=name[:-4], ticker=symbol.ticker, amount=free_asset) 
                    print(transaction_asset)
                    print("______________________________________________________________________________________")
                    transaction_quote = transfer_to_spot(asset="USDT", ticker=symbol.ticker, amount=free_quote)
                    print(transaction_quote)
                    symbol.has_position = False 
                else:
                    print("nothing borrowed: False")

            elif side=="BUY" and execution_type=="TRADE" and execution_status=="FILLED" and symbol.open_order == True: #check if order is filled 
                print('gekocht via de isolated socket')
                symbol.open_order = False
                symbol.log_buy(amount=symbol.piramidding_amount ,buy_price=symbol.buy_price, ticker=name, money=symbol.money)
                print(Fore.GREEN + f"{name} bought for {symbol.average_price} dollar. pirammiding at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                symbol.has_position = True
                transaction = transfer_to_isolated(asset="USDT", ticker=symbol.ticker, amount=1)

                asset = client.get_isolated_margin_account(symbols=name)
                symbol.amount = get_amount(float(asset["assets"][0]["baseAsset"]["free"]), symbol.precision)
                take_profit_order = send_order(side=SIDE_SELL , quantity=Decimal(symbol.amount), ticker=symbol.ticker,price=symbol.take_profit,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="AUTO_REPAY",timeInForce=TIME_IN_FORCE_GTC)
                if symbol.piramidding == False:
                    #check liquidation price and update stop loss, also add in direct fill for buy
                    symbol.liquidation_price = float(asset["assets"][0]["liquidatePrice"])
                    if symbol.liquidation_price > symbol.stop_loss:
                        symbol.stop_loss = symbol.liquidation_price *1.0075
        if event == "balanceUpdate":
            get_money()
        
    except Exception as e:
        now = dt.datetime.now()
        date = now.strftime("%d/%m/%Y")
        hour = now.strftime("%H:%M:%S")

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        file = open(error_log_file,"a")
        file.write(f'\n{date}\n{hour}\nan error occured: {e}\n{exc_type}\n{fname}\nLine: {exc_tb.tb_lineno}\n')
        file.close()

        #Database.insert_error_log(now, f"{e}\n{exc_type}", fname, f"{exc_tb.tb_lineno}")
        raise e

# endregion

if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print(f"Connected to Binance, server status: {status['msg']}")
    print("Fetching historical data.")
    # data = client.get_asset_balance(asset='USDT')
    # total_money = data["free"]
    get_money()
    instances = []
    for x in tqdm(range(len(tickers))):
        name = tickers[x][:-9].upper()
        globals()[name] = Ticker(name, log_file)
        symbol = globals()[name]
        instances.append(globals()[name]) 
        klines = client.get_historical_klines(name.upper(), interval=Client.KLINE_INTERVAL_1MINUTE, start_str="150 minutes ago CET", end_str='1 minutes ago CET')
        for k in klines:
            symbol.closes.append(float(k[4]))
            symbol.highs.append(float(k[2]))
            symbol.lows.append(float(k[3]))
            symbol.volumes.append(float(k[5]))
        # get margin ratio
        info = client.get_isolated_margin_account(symbols=name)
        symbol.margin_ratio = float(info["assets"][0]["marginRatio"])
        # print(name, " ratio: ",globals()[name].margin_ratio)
        # get precision
        symbol_info = client.get_symbol_info(name)
        for f in symbol_info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                symbol.precision = int(round(-math.log(step_size, 10), 0))
            elif f['filterType'] == "PRICE_FILTER":
                minPrice = float(f['minPrice'])
                symbol.precision_minPrice = int(round(-math.log(minPrice, 10), 0))
                # print(name, " precision: ",globals()[name].precision)
        # Database.update_ticker(ticker=name, datetime=dt.datetime.now(),shares=0.0, averagePrice=0.0, realizedpnl=0.0)
    print(f"Data fetched, you have {(total_money):.2f} dollar of buying power in your spot wallet.")

# initialize the socket when there is a connection
if str(client.ping()) == '{}':
    print("Intitialize listeners for isolated accounts.")
    for i in tqdm(instances):
        conn_key = bm.start_isolated_margin_socket(symbol=i.ticker, callback=callback_isolated_accounts)
    conn_key = bm.start_multiplex_socket(tickers, process_m_message)
    bm.start() #start the socket manager
    # print("5 sec sleep.")
    time.sleep(5)
    print("Program is running.")


# https://python-binance.readthedocs.io/en/latest/margin.html#orders
# when buy order is received -> send money to margin (Isolated if cross is not available)
# when sold -> transfer isolated margin back to spot wallet

# make sure time is synced in the beginning (look how to on pi)
# time.sleep()
# client.transfer_spot_to_isolated_margin(asset="USDT",symbol="UNFIUSDT", amount=23)


# send_order(side=SIDE_BUY , quantity=0.5, ticker="UNFIUSDT",price=24,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY",timeInForce=TIME_IN_FORCE_GTC)
