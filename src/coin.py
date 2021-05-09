import asyncio
from binance import AsyncClient
from concurrent.futures import CancelledError
import threading
import math
from time import sleep
from .constants import CANDLE_CLOSE, CANDLE_HIGH, CANDLE_LOW, CANDLE_VOLUME

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

    async def init(self):
        try:
            self.bot.create_isolated_margin_account(base = self.symbol_pair[:-4], quote = 'USDT')
        except Exception as e:
            self.bot.log.verbose('COIN', f'Isolated wallet exists for {self.symbol_pair}')

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

        s = self.bot.bm.isolated_margin_socket(self.symbol_pair)
        async with s as ts:
            while self._running:
                res = await ts.recv()
                if not res:
                    continue

                print(res)

    def update(self, candle):
        close = float(candle[CANDLE_CLOSE])
        high = float(candle[CANDLE_HIGH])
        low = float(candle[CANDLE_LOW])
        volume = float(candle[CANDLE_VOLUME])

        self.closes.append(close)
        self.highs.append(high)
        self.lows.append(low)
        self.volumes.append(volume)

