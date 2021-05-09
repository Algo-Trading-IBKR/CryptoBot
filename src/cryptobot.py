import asyncio
from binance import AsyncClient, BinanceSocketManager
import sys
from time import sleep
from src.util.logger import Log
from src.util.util import load_json
from .coin import Coin
from .order_manager import OrderManager
from .wallet import Wallet

class CryptoBot:
    def __init__(self):
        self._config = load_json('./configs/config.json')
        self._running = True

    @property
    def bm(self):
        return self._socket_manager

    @property
    def client(self):
        return self._client

    @property
    def config(self):
        return self._config

    @property
    def log(self):
        return Log

    async def start(self):
        self._active = self._config["configs"][self._config["active_config"]]

        Log.info('BOT', f"Using active config {self._active['name']}")
        Log.info('BOT', f"Using {len(self._config['pairs'])} coin pairs.")

        self._client = await AsyncClient.create(api_key=self._active["key"], api_secret=self._active["secret"])
        self._socket_manager = BinanceSocketManager(self._client) # user_timeout is now 5 minutes (5 * 60)

        status = await self._client.get_system_status()
        Log.info('BOT', f"System status: {status['msg']}")

        self._coins = [Coin(self, symbol_pair) for symbol_pair in self._config["pairs"]]
        self._order_manager = OrderManager(self)
        self._wallet = Wallet(self)

        Log.info('BOT', f"Total usable ${(await self._wallet.get_money()):.2f} in spot wallet.")

        self.tasks = [asyncio.create_task(coin.init()) for coin in self._coins]

        while self._running:
            await asyncio.sleep(0.1)
        await self._client.close_connection()

    def shutdown(self, signal, stack_frame):
        # gracefull shutdown, close positionts etc
        for task in self.tasks:
            task.cancel()

        self._running = False

        Log.info('BOT', 'Application exitted.')
