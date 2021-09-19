import asyncio
from concurrent.futures import CancelledError
import traceback
from .coin import Coin
from random import uniform
import math
import sys
from .constants import CANDLE, CANDLE_CLOSED, EVENT_TYPE, SYMBOL, TIMESTAMP

class CoinManager:
    def __init__(self, bot, active_pairs, inactive_pairs):
        self.bot = bot

        self._coins = {}

        for pair in active_pairs:
            coin = Coin(bot, pair["trade_symbol"], pair["currency_symbol"])
            self._coins[coin.symbol_pair] = coin

        for pair in inactive_pairs:
            coin = Coin(bot, pair["trade_symbol"], pair["currency_symbol"])
            self._coins[coin.symbol_pair] = coin
            coin.active = False

    def get_coin(self, symbol_pair, initcheck = True):
        if initcheck:
            if symbol_pair in self._coins and self._coins[symbol_pair].initialised:
                return self._coins[symbol_pair]
        else:
            if symbol_pair in self._coins:
                return self._coins[symbol_pair]
        return False

    async def process_message(self, msg):
        data = msg['data']

        if data[EVENT_TYPE] == 'error':
            self.bot.log.warning('BOT', 'Error on multiplex socket.')
            return

        candle = data[CANDLE]
        if candle[CANDLE_CLOSED]:
            coin = self.get_coin(data[SYMBOL])
            if coin:
                await coin.update(candle)

    async def init(self):
        try:
            tasks = []
            tasks.append(asyncio.create_task(self.start_multiplex()))
            tasks.append(asyncio.create_task(self.start_user_socket()))

            sleep_timer = 6 # this is safe using the rest api + caching

            for symbol in self.bot.exchange_info["data"]["symbols"]:
                coin = self.get_coin(symbol["symbol"], False)
                if coin:
                    for f in symbol['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            step_size = float(f['stepSize'])
                            coin.precision = round(-math.log(step_size, 10))
                        elif f['filterType'] == 'PRICE_FILTER':
                            min_price = float(f['minPrice'])
                            coin.precision_min_price = round(-math.log(min_price, 10))
                    self.bot.log.verbose('COIN_MANAGER', f'Got symbol info for {coin.symbol_pair}')

            for coin in self._coins.values():
                if coin.active:
                    await asyncio.sleep(sleep_timer)
                    tasks.append(asyncio.create_task(coin.init()))
        except Exception as e:
            print(str(e))

        self.bot.log.info('COIN_MANAGER', f'All coins and sockets initialised')
        return tasks

    async def start_multiplex(self):
        self._running = True
        self.bot.log.verbose('COIN_MANAGER', f'Starting multiplex socket')
        symbol_pairs = [symbol.lower() + '@kline_1h' for symbol in self._coins.keys()]
        async with self.bot.bm.multiplex_socket(symbol_pairs) as mps:
            try:
                while self._running:
                    res = await mps.recv()
                    if not res:
                        continue
                    await self.process_message(res)
            except (CancelledError,Exception) as e:
                if isinstance(e, CancelledError):
                    self._running = False
                self.bot.log.error('COIN_MANAGER', f'Error occured:\n{traceback.format_exc()}')

    async def start_user_socket(self):
        self._running = True
        self.bot.log.verbose('COIN_MANAGER', f'Starting user socket')
        
        s = self.bot.bm.user_socket()
        async with s as ts:
            while self._running:
                res = await ts.recv()
                if not res:
                    continue
                try:
                    if res['e'] == "executionReport":
                        coin = self.get_coin(res['s'])
                        if coin:
                            await coin.update_socket(res)
                    else:
                        self.bot.log.verbose('COIN_MANAGER', f'socket message {res}')
                        # sys.exit()

                except:
                    self.bot.log.error('COIN_MANAGER', f'Error occurred on socket:\n{traceback.format_exc()}')



