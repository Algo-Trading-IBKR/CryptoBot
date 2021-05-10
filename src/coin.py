import asyncio
from binance import AsyncClient
from binance.enums import ORDER_TYPE_LIMIT, SIDE_BUY, SIDE_SELL, TIME_IN_FORCE_GTC
from concurrent.futures import CancelledError
from decimal import Decimal
import threading
import math
import numpy as np
import talib
from time import sleep
from .constants import CANDLE_CLOSE, CANDLE_HIGH, CANDLE_LOW, CANDLE_VOLUME, EVENT_TYPE, EXECUTION_ERROR, EXECUTION_TYPE, EXECUTION_STATUS, EXECUTION_ORDER_ID, SIDE
from src.util.util import util

class Coin:
    def __init__(self, bot, symbol_pair : str):
        threading.Thread.__init__(self, daemon=True)

        self.bot = bot
        self.symbol_pair = symbol_pair

        # candles
        self.closes = []
        self.highs = []
        self.lows = []
        self.volumes = []

        self.margin_ratio = 0.0
        self.precision = 0
        self.precision_min_price = 0

        self.amount = 0.0
        self.buy_price = 0.0
        self.piramidding_amount = 0.0
        self.piramidding_price = 0.0

        self.has_open_order = False
        self.has_position = False
        self.is_piramidding = False

    @property
    def symbol():
        return self.symbol_pair[:-4]

    async def init(self):
        try:
            self.bot.create_isolated_margin_account(base = self.symbol, quote = 'USDT')
        except Exception as e:
            # self.bot.log.verbose('COIN', f'Isolated wallet exists for {self.symbol_pair}')
            pass

        candles = await self.bot.client.get_historical_klines(self.symbol_pair, interval = AsyncClient.KLINE_INTERVAL_1MINUTE, start_str = '150 minutes ago CET', end_str = '1 minutes ago CET')
        for candle in candles:
            self.closes.append(float(candle[4]))
            self.highs.append(float(candle[2]))
            self.lows.append(float(candle[3]))
            self.volumes.append(float(candle[5]))

        account = await self.bot.client.get_isolated_margin_account(symbols = self.symbol_pair)
        self.margin_ratio = float(account['assets'][0]['marginRatio'])

        info = await self.bot.client.get_symbol_info(self.symbol_pair)
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                self.precision = round(-math.log(step_size, 10))
            elif f['filterType'] == 'PRICE_FILTER':
                min_price = float(f['minPrice'])
                self.precision_min_price = round(-math.log(min_price, 10))

        try:
            await self.run()
        except CancelledError:
            self._running = False

    async def run(self):
        self._running = True

        self.bot.log.verbose('COIN', f'Starting isolated margin socket for {self.symbol_pair}')

        s = self.bot.bm.isolated_margin_socket(self.symbol_pair)
        async with s as ts:
            while self._running:
                res = await ts.recv()
                if not res:
                    continue

                await self.update_margin(res)

    async def update_margin(self, msg):
        event = msg[EVENT_TYPE]

        if event == 'executionReport':
            error = msg[EXECUTION_ERROR]
            if error is not None:
                self.bot.log.error('COIN', f'Execution Report error: {error}')

                return
            side = msg[SIDE]
            order_type = msg[ORDER_TYPE]
            execution_type = msg[EXECUTION_TYPE]
            execution_status = msg[EXECUTION_STATUS]
            order_id = msg[EXECUTION_ORDER_ID]

            if side == 'SELL' and execution_type == 'TRADE' and execution_status == 'FILLED' and self.bot.order_manager.has_order_id(self.symbol_pair, order_id):
                self.bot.log.verbose('COIN', f'Filled SELL order for {self.symbol_pair}')

                self.is_piramidding = False
                await asyncio.sleep(2)

                account = await self.bot.client.get_isolated_margin_account(symbol = self.symbol_pair)
                free_asset, borrowed_asset, free_quote, borrowed_quote = util.get_asset_and_quote(account)

                self.has_position = False

                if borrowed_asset == 0 and borrowed_quote == 0:
                    transaction_asset = await self.bot.wallet.transfer_to_spot(self.symbol, self.symbol_pair, free_asset)
                    transaction_quote = await self.bot.wallet.transfer_to_spot('USDT', self.symbol_pair, free_quote)
            elif side == 'BUY' and execution_type == 'TRADE'  and execution_status == 'FILLED' and self.has_open_order:
                self.bot.log.verbose('COIN', f'Filled BUY order for {self.symbol_pair}')

                self.has_open_order = False
                self.has_position = True

                transaction = await self.bot.wallet.transfer_to_isolated('USDT', self.symbol_pair, 1)

                account = await self.bot.client.get_isolated_margin_account(symbol = self.symbol_pair)
                self.amount = util.get_amount(float(account['assets'][0]['baseAsset']['free'], self.precision))

                take_profit_order = await self.bot.order_manager.send_order(
                    coin = self,
                    side = SIDE_SELL,
                    quantity = Decimal(self.amount),
                    price = self.take_profit,
                    order_type = ORDER_TYPE_LIMIT,
                    isolated = True,
                    side_effect = 'AUTO_REPAY',
                    time_in_force = TIME_IN_FORCE_GTC
                )

                if not self.is_piramidding:
                    #check liquidation price and update stop loss, also add in direct fill for buy
                    self.liquidation_price = float(account["assets"][0]["liquidatePrice"])
                    if self.liquidation_price > self.piramidding_price:
                        self.piramidding_price = self.liquidation_price * 1.0075
        if event == 'balanceUpdate':
            self.bot.log.verbose('COIN', 'Got balance update from isolated margin account.')

            await self.bot.wallet.update_money()

    async def update(self, candle):
        close = float(candle[CANDLE_CLOSE])
        high = float(candle[CANDLE_HIGH])
        low = float(candle[CANDLE_LOW])
        volume = float(candle[CANDLE_VOLUME])

        self.closes.append(close)
        self.highs.append(high)
        self.lows.append(low)
        self.volumes.append(volume)

        if len(self.closes) <= 149:
            return

        rsi = talib.RSI(np.array(self.closes), timeperiod=self.bot.config["indicators"]["rsi"]["period"])
        mfi = talib.MFI(
            np.array(self.highs),
            np.array(self.lows),
            np.array(self.closes),
            np.array(self.volumes),
            timeperiod=self.bot.config["indicators"]["mfi"]["period"]
        )

        last_rsi = rsi[-1]
        last_mfi = mfi[-1]

        if self.has_open_order:
            self.has_open_order = False

            await self.bot.order_manager.cancel_order(self)

            account = await self.bot.client.get_isolated_margin_account(self.symbol_pair)
            free_asset, borrowed_asset, free_quote, borrowed_quote = util.get_asset_and_quote(account)

            transaction = await self.bot.client.repay_margin_loan(asset='USDT', amount=borrowed_quote, isIsolated=True, symbol = self.symbol_pair)

            if free_asset > 0:
                transaction_asset = await self.bot.wallet.transfer_to_spot(self.symbol, self.symbol_pair, free_asset)
            if free_quote > 0:
                transaction_quote = await self.bot.wallet.transfer_to_spot(self.symbol, self.symbol_pair, free_quote - borrowed_quote)

            self.has_position = False
            self.is_piramidding = False

        # sell
        if self.has_position:
            current_price = self.closes[-1]
            current_high = self.highs[-1]

            await self.bot.wallet.update_money()

            order_succeeded = False

            if current_price < self.piramidding_price and self.bot.wallet.money >= (self.bot.active["budget"] + self.bot.active["minimum_cash"]) and not self.is_piramidding:
                transaction = self.bot.wallet.transfer_to_isolated('USDT', self.symbol_pair, self.bot.active["budget"])

                self.is_piramidding = True

                account = await self.bot.client.get_isolated_margin_account(symbol = self.symbol_pair)
                free_asset, borrowed_asset, free_quote, borrowed_quote = util.get_asset_and_quote(account)

                if free_quote >= self.bot.active["budget"]:
                    self.bot.log.verbose('COIN', 'free_asset {free_asset}, borrowed_asset {borrowed_asset}, free_quote {free_quote}, borrowed_quote {borrowed_quote}')

                    self.bot.order_manager.cancel_order(self)

                    self.piramidding_amount = util.get_amount((self.bot.active["budget"] / self.bot.active["budget_divider"]) / current_price, self.precision)
                    self.buy_price = current_price

                    order_succeeded = await self.bot.order_manager.send_order(
                        coin = self,
                        side = SIDE_BUY,
                        quantity = Decimal(self.piramidding_amount * self.margin_ratio),
                        price = current_price,
                        order_type = ORDER_TYPE_LIMIT,
                        isolated = True,
                        side_effect = 'MARGIN_BUY',
                        time_in_force = TIME_IN_FORCE_GTC
                    )
                    self.average_price_piramidding = (self.amount * self.average_price + self.piramidding_amount * current_price) / (self.amount + self.piramidding_amount)
                    self.take_profit = util.get_amount(self.average_price_piramidding * self.bot.config["strategy"]["take_profit_percentage"], self.precision_min_price, False)

                    if order_succeeded:
                        account = await self.bot.client.get_isolated_margin_account(symbol=self.symbol_pair)
                        self.amount = util.get_amount(float(account["assets"][0]["baseAsset"]["free"]), self.precision)

                        take_profit_order = await self.bot.order_manager.send_order(
                            coin = self,
                            side = SIDE_SELL,
                            quantity = Decimal(self.amount),
                            price = self.take_profit,
                            order_type = ORDER_TYPE_LIMIT,
                            isolated = True,
                            side_effect = 'AUTO_REPAY',
                            time_in_force = TIME_IN_FORCE_GTC
                        )
                        self.has_position = True
                elif free_quote < budget:
                    self.bot.log.warning('COIN', f'Failed to piramid for {self.symbol_pair}, not enough money.')

        # buy
        elif (
            last_rsi < self.bot.config["indicators"]["rsi"]["oversold"] and
            last_mfi < self.bot.config["indicators"]["mfi"]["oversold"] and
            self.bot.wallet.money >= (self.bot.active["budget"] + self.bot.active["minimum_cash"])
        ):
            self.bot.log.verbose('COIN', f'Starting buy for {self.symbol_pair}')

            transaction = await self.bot.wallet.transfer_to_isolated('USDT', self.symbol_pair, self.bot.active["budget"])

            self.average_price = self.closes[-1]
            self.amount = util.get_amount((self.bot.active["budget"] / self.bot.active["budget_divider"]) / self.average_price, self.precision)

            self.piramidding_price = await self.bot.order_manager.get_low(self.symbol_pair)
            if self.piramidding_price > (self.average_price - self.average_price * 0.06):
                self.piramidding_price = self.average_price - self.average_price * 0.06

            self.take_profit = util.get_amount(self.average_price * self.bot.config["strategy"]["take_profit_percentage"], self.precision_min_price, False)

            self.buy_price = self.average_price
            await asyncio.sleep(0.1)
            order_succeeded = await self.bot.order_manager.send_order(
                coin = self,
                side = SIDE_BUY,
                quantity = Decimal(self.amount * self.margin_ratio),
                price = self.average_price,
                order_type = ORDER_TYPE_LIMIT,
                isolated = True,
                side_effect = 'MARGIN_BUY',
                time_in_force = TIME_IN_FORCE_GTC
            )

            if order_succeeded:
                self.bot.log.verbose('COIN', f'Buy order filled for {self.symbol_pair}')

                self.has_position = True

                transaction = await self.bot.wallet.transfer_to_isolated('USDT', self.symbol_pair, 1)

                account = await self.bot.client.get_isolated_margin_account(symbol = self.symbol_pair)
                self.amount = util.get_amount(float(account['assets'][0]['baseAsset']['free']), self.precision)
                take_profit_order = await self.bot.order_manager.send_order(
                    coin = self,
                    side = SIDE_SELL,
                    quantity = Decimal(self.amount),
                    price = self.take_profit,
                    order_type = ORDER_TYPE_LIMIT,
                    isolated = True,
                    side_effect = 'AUTO_REPAY',
                    time_in_force = TIME_IN_FORCE_GTC
                )

                self.liquidation_price = float(account['assets'][0]['liquidatePrice'])
                if self.liquidation_price > self.piramidding_price:
                    self.piramidding_price = self.liquidation_price * 1.0075

        self.closes = self.closes[-150:]
        self.highs = self.highs[-150:]
        self.lows = self.lows[-150:]
        self.volumes = self.volumes[-150:]
