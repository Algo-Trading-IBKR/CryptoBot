import asyncio
from concurrent.futures import CancelledError
import traceback
from .coin import Coin
from .constants import CANDLE, CANDLE_CLOSED, EVENT_TYPE, SYMBOL, TIMESTAMP

class CoinManager:
    def __init__(self, bot, pairs):
        self.bot = bot

        self._coins = {}

        for pair in pairs:
            self._coins[pair] = Coin(bot, pair)

    def get_coin(self, symbol_pair):
        return self._coins[symbol_pair]

    async def process_message(self, msg):
        data = msg['data']

        if data[EVENT_TYPE] == 'error':
            self.bot.log.warning('BOT', 'Error on multiplex socket.')
            return

        candle = data[CANDLE]
        if candle[CANDLE_CLOSED]:
            coin = self.get_coin(data[SYMBOL])
            await coin.update(candle)

    def init(self):
        tasks = [asyncio.create_task(coin.init()) for coin in self._coins.values()]
        tasks.append(self.init_multiplex())

        return tasks

    def init_multiplex(self):
        return asyncio.create_task(self.start_multiplex())

    async def start_multiplex(self):
        self._running = True

        symbol_pairs = [symbol.lower() + '@kline_1m' for symbol in self._coins.keys()]
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

