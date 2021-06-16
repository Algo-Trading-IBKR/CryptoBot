import asyncio
from binance import AsyncClient
from binance.enums import ORDER_TYPE_LIMIT, SIDE_BUY, SIDE_SELL, TIME_IN_FORCE_GTC
from concurrent.futures import CancelledError
from decimal import Decimal
import threading
import math
import numpy as np
from pymongo import DESCENDING
import talib
import traceback
import requests
from datetime import datetime
from .constants import CANDLE_CLOSE, CANDLE_HIGH, CANDLE_LOW, CANDLE_VOLUME, EVENT_TYPE, EXECUTION_ERROR, EXECUTION_TYPE, EXECUTION_STATUS, EXECUTION_ORDER_ID, ORDER_TYPE, SIDE, SYMBOL, CANDLE_CLOSED
from src.util.util import util

class Coin:
    def __init__(self, bot, trade_symbol : str, currency_symbol : str):
        threading.Thread.__init__(self, daemon=True)

        self.bot = bot

        self.currency_symbol = currency_symbol
        self.trade_symbol = trade_symbol

        # candles
        self.closes = []
        self.highs = []
        self.lows = []
        self.volumes = []

        self.precision = 0
        self.precision_min_price = 0

        self.amount = 0.0
        self.buy_price = 0.0
        self.piramidding_amount = 0.0
        self.piramidding_price = 0.0

        self.has_open_order = False
        self.has_position = False
        self.allow_piramidding = False

        self.initialised = False

        self.wallet_counter = 0

    @property
    def currency(self):
        return self.currency_symbol

    @property
    def symbol(self):
        return self.trade_symbol

    @property
    def symbol_pair(self):
        return self.trade_symbol + self.currency_symbol

    async def init(self):
        try:
            self.bot.log.verbose('COIN', f'init')

            # info = await self.bot.client.get_symbol_info(self.symbol_pair)
            # for f in info['filters']:
            #     if f['filterType'] == 'LOT_SIZE':
            #         step_size = float(f['stepSize'])
            #         self.precision = round(-math.log(step_size, 10))
            #     elif f['filterType'] == 'PRICE_FILTER':
            #         min_price = float(f['minPrice'])
            #         self.precision_min_price = round(-math.log(min_price, 10))

            # self.bot.log.verbose('COIN', f'Got symbol info for {self.symbol_pair}')

            await self.get_open_orders()

            params = {'api_secret': self.bot.user["api_keys"]["secret"],
                    'symbol_pair': self.symbol_pair,
                    'kline_interval': '1h',
                    'length': 150*60*60*1000} # amount of candles * minutes * seconds * millis

            url = self.bot.api_url + "/binance/historicalklines"
            info = requests.get(url=url, params=params)
            candles = info.json()["data"]
            
            # candles = await self.bot.client.get_historical_klines(self.symbol_pair, interval = AsyncClient.KLINE_INTERVAL_1HOUR, start_str = f'{150*60} minutes ago CET', end_str = '1 minutes ago CET')
            for candle in candles:
                self.closes.append(float(candle[4]))
                self.highs.append(float(candle[2]))
                self.lows.append(float(candle[3]))
                self.volumes.append(float(candle[5]))

            self.bot.log.verbose('COIN', f'Fetched historical klines for {self.symbol_pair}')
            self.initialised = True
        except Exception as e:
            print(str(e))
     
    async def get_open_orders(self):
        try:
            orders = await self.bot.client.get_all_orders(symbol = self.symbol_pair, limit=1)
            if len(orders) > 0:
                order = orders[0]
                if order and order["clientOrderId"].startswith("CryptoBot"):
                    if order["side"] == "BUY":
                        if order["status"] == "NEW":
                            self.bot.order_manager.order_book.set_order_for_symbol(self.symbol_pair, order['side'], order['orderId'])
                            self.has_open_order = True
                        elif order["status"] == "FILLED":
                            self.bot.log.info('COIN', f'{order["side"]} order filled for {self.symbol_pair}')
                            self.has_position = True

                            asset = await self.bot.client.get_asset_balance(self.symbol)
                            if float(asset['free']) > 0:
                                self.amount = util.get_amount(float(asset['free']), self.precision)
                                self.take_profit = util.get_amount(float(order["price"]) * self.bot.user["strategy"]["take_profit_percentage"], self.precision_min_price, False)

                                take_profit_order = await self.bot.order_manager.send_order(
                                    coin = self,
                                    side = SIDE_SELL,
                                    quantity = Decimal(self.amount),
                                    price = self.take_profit,
                                    order_type = ORDER_TYPE_LIMIT,
                                    time_in_force = TIME_IN_FORCE_GTC
                                )
                                self.piramidding_price = float(order["price"]) * self.bot.user["strategy"]["piramidding_percentage"]

                    elif order["side"] == "SELL":
                        if order["status"] == "NEW":
                            self.bot.order_manager.order_book.set_order_for_symbol(self.symbol_pair, order['side'], order['orderId'])
                            self.has_position = True
                        elif order["status"] == "FILLED":
                            self.has_position = False
        except Exception as e:
            self.bot.log.error('COIN', f'startup failed for {self.symbol_pair} on get open orders {str(e)}')

    async def update_socket(self, msg):
        error = msg[EXECUTION_ERROR]
        if error != 'NONE':
            self.bot.log.error('COIN', f'Execution Report error: {error}')
            return

        side = msg[SIDE]
        order_type = msg[ORDER_TYPE]
        execution_type = msg[EXECUTION_TYPE]
        execution_status = msg[EXECUTION_STATUS]
        order_id = msg[EXECUTION_ORDER_ID]

        if execution_type == 'TRADE' and execution_status == 'FILLED':
            try:
                order = await self.bot.client.get_order(symbol = msg[SYMBOL], orderId = order_id)
                old_order = self.bot.mongo.cryptobot.orders.find_one({"orderId": order_id})
                if old_order:
                    order.update({"discord_id": self.bot.user["discord_id"]})
                    order.update({"datetime": datetime.now()})
                    # self.bot.log.info('COIN', f'order: {order}')
                    self.bot.mongo.cryptobot.orders.replace_one(old_order, order, upsert=True)
            except Exception as e:
                self.bot.log.info('COIN', f'update mongo trade failed: {str(e)}')


            if side == 'SELL' and self.bot.order_manager.has_order_id(self.symbol_pair, order_id):
                self.bot.log.info('COIN', f'Filled {side} order for {self.symbol_pair}')
                self.allow_piramidding = False
                await asyncio.sleep(0.1) # why?
                self.has_position = False

            elif side == 'BUY' and self.has_open_order:
                self.bot.log.info('COIN', f'Filled {side} order for {self.symbol_pair}')

                self.has_open_order = False
                self.has_position = True

                asset = await self.bot.client.get_asset_balance(self.symbol)
                self.amount = util.get_amount(float(asset['free']), self.precision)

                take_profit_order = await self.bot.order_manager.send_order(
                    coin = self,
                    side = SIDE_SELL,
                    quantity = Decimal(self.amount),
                    price = self.take_profit,
                    order_type = ORDER_TYPE_LIMIT,
                    time_in_force = TIME_IN_FORCE_GTC
                )

                if not self.allow_piramidding:
                    self.piramidding_price = self.average_price * self.bot.user["strategy"]["piramidding_percentage"]
            
            await self.bot.wallet.update_money(self.currency)
        
    async def update(self, candle):
        close = float(candle[CANDLE_CLOSE])
        high = float(candle[CANDLE_HIGH])
        low = float(candle[CANDLE_LOW])
        volume = float(candle[CANDLE_VOLUME])
        #region constant updates
        # if candle[CANDLE_CLOSED]:
        #     self.closes.append(close)
        #     self.highs.append(high)
        #     self.lows.append(low)
        #     self.volumes.append(volume)

        #     if len(self.closes) <= 149:
        #         return

        #     rsi = talib.RSI(np.array(self.closes), timeperiod=self.bot.indicators["rsi"]["period"])
        #     mfi = talib.MFI(
        #         np.array(self.highs),
        #         np.array(self.lows),
        #         np.array(self.closes),
        #         np.array(self.volumes),
        #         timeperiod=self.bot.indicators["mfi"]["period"]
        #     )

        #     last_rsi = rsi[-1]
        #     last_mfi = mfi[-1]
        # else: 
        #     temp_close = self.closes
        #     temp_high = self.closes
        #     temp_low = self.closes
        #     temp_volume = self.closes

        #     temp_close.append(close)
        #     temp_high.append(high)
        #     temp_low.append(low)
        #     temp_volume.append(volume)

        #     if len(temp_close) <= 149:
        #         return
        #     rsi = talib.RSI(np.array(temp_close), timeperiod=self.bot.indicators["rsi"]["period"])
        #     mfi = talib.MFI(
        #         np.array(temp_high),
        #         np.array(temp_low),
        #         np.array(temp_close),
        #         np.array(temp_volume),
        #         timeperiod=self.bot.indicators["mfi"]["period"]
        #     )

        #     last_rsi = rsi[-1]
        #     last_mfi = mfi[-1]
        #endregion

        self.closes.append(close)
        self.highs.append(high)
        self.lows.append(low)
        self.volumes.append(volume)

        if len(self.closes) <= 149:
            return

        rsi = talib.RSI(np.array(self.closes), timeperiod=self.bot.indicators["rsi"]["period"])
        mfi = talib.MFI(
            np.array(self.highs),
            np.array(self.lows),
            np.array(self.closes),
            np.array(self.volumes),
            timeperiod=self.bot.indicators["mfi"]["period"]
        )

        last_rsi = rsi[-1]
        last_mfi = mfi[-1]

        if self.has_open_order:
            canceled = await self.bot.order_manager.cancel_order(self, 'BUY')
            if canceled:
                self.has_open_order = False
                self.has_position = False
                self.allow_piramidding = False
            # else:
            #     self.has_open_order = True
            #     self.has_position = False
            #     self.allow_piramidding = False
            await self.bot.wallet.update_money(self.currency)

        # sell
        if self.has_position:
            # if candle[CANDLE_CLOSED]:
            #     current_price = self.closes[-1]
            # else:
            #     current_price = temp_close[-1]
            current_price = self.closes[-1]

            order_succeeded = False

            if current_price < self.piramidding_price and not self.allow_piramidding:
                await self.bot.wallet.update_money(self.currency)
                if self.bot.wallet.money[self.currency] >= (self.bot.user["wallet"]["budget"] + self.bot.user["wallet"]["minimum_cash"]): 

                    self.allow_piramidding = True

                    # asset = await self.bot.client.get_asset_balance(self.symbol)
                    # self.amount = util.get_amount(float(asset['free']), self.precision)

                    await self.bot.order_manager.cancel_order(self, 'SELL')

                    self.piramidding_amount = util.get_amount(self.bot.user["wallet"]["budget"] / current_price, self.precision)
                    self.buy_price = current_price

                    order_succeeded = await self.bot.order_manager.send_order(
                        coin = self,
                        side = SIDE_BUY,
                        quantity = Decimal(self.piramidding_amount),
                        price = current_price,
                        order_type = ORDER_TYPE_LIMIT,
                        time_in_force = TIME_IN_FORCE_GTC,
                        piramidding=True
                    )

                    self.average_price_piramidding = (self.amount * self.average_price + self.piramidding_amount * current_price) / (self.amount + self.piramidding_amount)
                    self.take_profit = util.get_amount(self.average_price_piramidding * self.bot.user["strategy"]["take_profit_percentage"], self.precision_min_price, False)

                    if order_succeeded:
                        asset = await self.bot.client.get_asset_balance(self.symbol)
                        self.amount = util.get_amount(float(asset['free']), self.precision)

                        take_profit_order = await self.bot.order_manager.send_order(
                            coin = self,
                            side = SIDE_SELL,
                            quantity = Decimal(self.amount),
                            price = self.take_profit,
                            order_type = ORDER_TYPE_LIMIT,
                            time_in_force = TIME_IN_FORCE_GTC
                        )
                        self.has_position = True
            elif current_price < self.piramidding_price and self.bot.wallet.money[self.currency] < (self.bot.user["wallet"]["budget"] + self.bot.user["wallet"]["minimum_cash"]):
                self.bot.log.warning('COIN', f'Failed to piramid for {self.symbol_pair}, not enough money.')

        # buy
        elif (
            last_rsi < self.bot.indicators["rsi"]["oversold"] and
            last_mfi < self.bot.indicators["mfi"]["oversold"]   
        ):
            await self.bot.wallet.update_money(self.currency)
            if self.bot.wallet.money[self.currency] >= (self.bot.user["wallet"]["budget"] + self.bot.user["wallet"]["minimum_cash"]):
                self.bot.log.verbose('COIN', f'Starting buy for {self.symbol_pair}')

                # if candle[CANDLE_CLOSED]:
                #     self.average_price = self.closes[-1]
                # else:
                #     self.average_price = temp_close[-1]
                self.average_price = self.closes[-1]
                    
                self.amount = util.get_amount(self.bot.user["wallet"]["budget"] / self.average_price, self.precision)

                self.piramidding_price = self.average_price * self.bot.user["strategy"]["piramidding_percentage"]

                self.take_profit = util.get_amount(self.average_price * self.bot.user["strategy"]["take_profit_percentage"], self.precision_min_price, False)

                self.buy_price = self.average_price
                # await asyncio.sleep(0.1)
                order_succeeded = await self.bot.order_manager.send_order(
                    coin = self,
                    side = SIDE_BUY,
                    quantity = Decimal(self.amount),
                    price = self.buy_price,
                    order_type = ORDER_TYPE_LIMIT,
                    time_in_force = TIME_IN_FORCE_GTC
                )

                if order_succeeded:
                    self.bot.log.info('COIN', f'Buy order filled for {self.symbol_pair}')

                    self.has_position = True

                    asset = await self.bot.client.get_asset_balance(self.symbol)
                    self.amount = util.get_amount(float(asset['free']), self.precision)

                    take_profit_order = await self.bot.order_manager.send_order(
                        coin = self,
                        side = SIDE_SELL,
                        quantity = Decimal(self.amount),
                        price = self.take_profit,
                        order_type = ORDER_TYPE_LIMIT,
                        time_in_force = TIME_IN_FORCE_GTC
                    )

                    self.piramidding_price = self.average_price * self.bot.user["strategy"]["piramidding_percentage"]

        self.closes = self.closes[-150:]
        self.highs = self.highs[-150:]
        self.lows = self.lows[-150:]
        self.volumes = self.volumes[-150:]