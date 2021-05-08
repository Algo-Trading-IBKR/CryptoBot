import asyncio
from binance import AsyncClient
from concurrent.futures import CancelledError
import threading
import math
from time import sleep

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

    @asyncio.coroutine
    def init(self):
        try:
            self.bot.create_isolated_margin_account(base = self.symbol_pair[:-4], quote = 'USDT')
        except Exception as e:
            self.bot.log.verbose(self.symbol_pair, 'Isolated wallet already exists.')

        candles = yield from self.bot.client.get_historical_klines(self.symbol_pair, interval = AsyncClient.KLINE_INTERVAL_1MINUTE, start_str = '150 minutes ago CET', end_str = '1 minutes ago CET')
        for candle in candles:
            self.closes.append(float(candle[4]))
            self.highs.append(float(candle[2]))
            self.lows.append(float(candle[3]))
            self.volumes.append(float(candle[5]))

        info = yield from self.bot.client.get_isolated_margin_account(symbols = self.symbol_pair)
        self.margin_ratio = float(info['assets'][0]['marginRatio'])

        info = yield from self.bot.client.get_symbol_info(self.symbol_pair)
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                self.precision = round(-math.log(step_size, 10))
            elif f['filterType'] == 'PRICE_FILTER':
                min_price = float(f['minPrice'])
                self.precision_min_price = round(-math.log(min_price, 10))

        yield from self.run()

    @asyncio.coroutine
    def run(self):
        ts = self.bot.bm.isolated_margin_socket(self.symbol_pair)
        while True:
            try:
                res = yield from ts.recv()
                if not res:
                    yield from asyncio.sleep(0.01)
                    continue

                print(res)
            except CancelledError:
                ts.close_connection()

                break


