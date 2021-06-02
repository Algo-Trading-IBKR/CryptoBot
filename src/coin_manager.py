import asyncio
from concurrent.futures import CancelledError
import traceback
from .coin import Coin
from random import uniform
from .constants import CANDLE, CANDLE_CLOSED, EVENT_TYPE, SYMBOL, TIMESTAMP

class CoinManager:
    def __init__(self, bot, pairs):
        self.bot = bot

        self._coins = {}

        for pair in pairs:
            coin = Coin(bot, pair["trade_symbol"], pair["currency_symbol"])
            self._coins[coin.symbol_pair] = coin

    def get_coin(self, symbol_pair):
        if symbol_pair in self._coins and self._coins[symbol_pair].initialised:
            return self._coins[symbol_pair]
        else:
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

    async def init(self, user_count):
        tasks = []
        tasks.append(asyncio.create_task(self.start_multiplex()))
        tasks.append(asyncio.create_task(self.start_user_socket()))

        sleep_timer = uniform(5,user_count*2)

        for coin in self._coins.values():
            await asyncio.sleep(sleep_timer)
            tasks.append(asyncio.create_task(coin.init()))

        self.bot.log.info('COIN_MANAGER', f'All coins and sockets initialised')
        return tasks

    async def start_multiplex(self):
        self._running = True
        self.bot.log.verbose('COIN_MANAGER', f'Starting multiplex socket')
        symbol_pairs = [symbol.lower() + '@kline_15m' for symbol in self._coins.keys()]
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

                except:
                    self.bot.log.error('COIN_MANAGER', f'Error occurred on socket:\n{traceback.format_exc()}')

