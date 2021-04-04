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



if str(client.ping()) == '{}': #{} means that it is connected
    status = client.get_system_status()
    print("Connected to Binance, server status:", status["msg"])
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
        # get margin ratio
        info = client.get_isolated_margin_account(symbols=name)
        globals()[name].margin_ratio = info["assets"][0]["marginRatio"]
        # print(name, " ratio: ",globals()[name].margin_ratio)
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

def get_amount(number:float, decimals:int=2):
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor

# orders
# side effect: AUTO_REPAY, MARGIN_BUY
def send_order(side, quantity, ticker, price, order_type, isolated, side_effect):
    symbol = globals()[ticker]
    global total_money
    try:
        print("Sending order...")
        # print("limit order")
        order = client.create_margin_order(side=side, quantity=quantity, symbol=ticker, price=price, type=order_type, isIsolated=isolated, sideEffectType=side_effect, timeInForce=TIME_IN_FORCE_FOK)
        print(order)
        if order["status"] == "FILLED":
            if order["side"] == "SELL":
                symbol.TP_order_ID = order['orderId'] #instantie
            return True
        else:
            return False
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    total_money = get_money()

def cancel_order(ticker,order_id):
    try:
        print("Cancelling order...")
        result = client.cancel_margin_order(symbol=ticker,orderId=order_id,isIsolated="TRUE")        
        print(result)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False
    return True

# transfer
def transfer_to_isolated(asset, ticker, amount):
    global total_money
    t = client.transfer_spot_to_isolated_margin(asset=asset,symbol=ticker, amount=amount)
    total_money = get_money()
    return t

def transfer_to_spot(asset, ticker, amount):
    global total_money
    t = client.transfer_isolated_margin_to_spot(asset=asset,symbol=ticker, amount=amount)
    total_money = get_money()
    return t


# endregion

# region callbacks
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

                    verkopen
                    if symbol.has_position:
                        current_price = symbol.closes[-1]
                        current_high = symbol.highs[-1]
                        order_succeeded = False

                        # # sell with a profit
                        # if current_high > float(symbol.take_profit):
                        #     print(Fore.RED + f"{name} sold with a profit.")
                        #     symbol.money += symbol.amount * symbol.take_profit
                        #     symbol.log_sell(profit=True ,price=symbol.take_profit ,ticker=name ,amount=symbol.amount ,money=symbol.money)
                        #     order_succeeded = True
                        #     symbol.amount = 0
                        #     if order_succeeded:
                        #         symbol.has_position = False
                        #         order_succeeded = False

                        
                        # sell with a loss of initiate piramiding
                        if current_price < float(symbol.stop_loss):
                            # piramidding
                            asset = client.get_isolated_margin_account(symbols=name)
                            free_asset, borrowed_asset = asset["assets"][0]["baseAsset"]["free"], asset["assets"][0]["baseAsset"]["borrowed"]
                            free_quote, borrowed_quote = asset["assets"][0]["quoteAsset"]["free"], asset["assets"][0]["quoteAsset"]["borrowed"]  
                            # 11 -> half of buy amount (add in config)
                            if free_quote >= 11:
                                print(Fore.RED  +f"{name} price dropped under the stop loss, buy a second time.")
                                piramidding_amount = get_amount((22/2)/current_price, symbol.precision)
                                # calculate average price after buy to send new TP order
                                










                            if float(symbol.money) > 20:
                                
                                piramidding_amount = symbol.money/current_price
                                symbol.average_price = (symbol.amount*symbol.average_price + piramidding_amount*current_price) / (symbol.amount+piramidding_amount)
                                symbol.log_buy(amount=piramidding_amount ,buy_price=current_price, ticker=name, money=symbol.money)
                                symbol.amount += piramidding_amount
                                symbol.stop_loss = get_low(symbol.ticker)
                                if float(symbol.stop_loss) > (symbol.average_price - (symbol.average_price*0.05)):
                                    symbol.stop_loss = symbol.average_price - (symbol.average_price*0.05)
                                symbol.take_profit = symbol.average_price * 1.012
                                symbol.money -= current_price * piramidding_amount
                                order_succeeded = True

                                if order_succeeded:
                                    print(Fore.GREEN + f"SECOND BUY: {name} bought for {current_price} dollar. Stop loss at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                                    try:
                                        response = clickatell.sendMessage(to=phone_numbers, message=f"SECOND BUY: {name} bought for {current_price} dollar.")
                                    except Exception as e:
                                        pass
                                    symbol.has_position = True
                                    order_succeeded = False

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
                            transaction = transfer_to_isolated(asset="USDT", ticker=symbol.ticker, amount=22)
                            symbol.average_price = symbol.closes[-1] #get the wanted buy price 
                            symbol.amount = get_amount((22/2)/symbol.average_price, symbol.precision) #get amount the bot could buy
                            symbol.stop_loss = get_low(symbol.ticker) #get a stop loss
                            if float(symbol.stop_loss) > (symbol.average_price - (symbol.average_price*0.03)):
                                symbol.stop_loss = symbol.average_price - (symbol.average_price*0.03)
                            symbol.take_profit = symbol.average_price * 1.011 #get a take profit amount

                            order_succeeded = send_order(side=SIDE_BUY , quantity=symbol.amount*symbol.margin_ratio, ticker=symbol.ticker,price=symbol.average_price,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="MARGIN_BUY")
                            print(order_succeeded)

                            if order_succeeded:
                                # log buy 
                                symbol.log_buy(amount=symbol.amount ,buy_price=symbol.average_price, ticker=name, money=symbol.money)
                                print(Fore.GREEN + f"{name} bought for {symbol.average_price} dollar. rsi: {last_rsi} mfi: {last_mfi}. pirammiding at {symbol.stop_loss} and take profit at {symbol.take_profit}")
                                symbol.has_position = True
                                order_succeeded = False

                                # get amount in wallet
                                asset = client.get_isolated_margin_account(symbols=name)
                                symbol.amount = get_amount(float(asset["assets"][0]["baseAsset"]["free"]), symbol.precision)
                                take_profit_order = send_order(side=SIDE_SELL , quantity=symbol.amount, ticker=symbol.ticker,price=symbol.take_profit,order_type=ORDER_TYPE_LIMIT,isolated=True,side_effect="AUTO_REPAY")
                                
                
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

            
def callback_isolated_accounts(msg):
    # sell function here https://binance-docs.github.io/apidocs/spot/en/#payload-balance-update
    # check if any are still borrowed 
    global total_money
    print(msg)
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
            asset = client.get_isolated_margin_account(symbols=name)
            free_asset, borrowed_asset = asset["assets"][0]["baseAsset"]["free"], asset["assets"][0]["baseAsset"]["borrowed"]
            free_quote, borrowed_quote = asset["assets"][0]["quoteAsset"]["free"], asset["assets"][0]["quoteAsset"]["borrowed"]
            if borrowed_asset == 0 and borrowed_quote == 0: 
                #transaction to spot
                transaction_asset = transfer_to_spot(asset=name[:-4], ticker=symbol.ticker, amount=free_asset) 
                transaction_quote = transfer_to_spot(asset="USDT", ticker=symbol.ticker, amount=free_quote) 
            



# endregion

# initialize the socket when there is a connection
if str(client.ping()) == '{}':
    print("Intitialize listeners for isolated accounts.")
    for i in tqdm(instances):
        conn_key = bm.start_isolated_margin_socket(symbol=i.ticker, callback=callback_isolated_accounts)
    conn_key = bm.start_multiplex_socket(tickers, process_m_message)
    bm.start() #start the socket manager
    print("Program is running.")


# https://python-binance.readthedocs.io/en/latest/margin.html#orders
# when buy order is received -> send money to margin (Isolated if cross is not available)
# when sold -> transfer isolated margin back to spot wallet

# make sure time is synced in the beginning (look how to on pi)
