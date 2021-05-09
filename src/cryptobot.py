import asyncio
from binance import AsyncClient, BinanceSocketManager
import sys
from time import sleep
from src.util.logger import Log
from src.util.util import load_json
from .coin_manager import CoinManager
from .order_manager import OrderManager
from .wallet import Wallet

class CryptoBot:
    def __init__(self):
        self._config = load_json('./configs/config.json')
        self._running = True

        self.tasks = []

    @property
    def bm(self) -> BinanceSocketManager:
        return self._socket_manager

    @property
    def client(self) -> AsyncClient:
        return self._client

    @property
    def config(self):
        return self._config

    @property
    def log(self) -> Log:
        return Log

    async def start(self):
        self._active = self._config["configs"][self._config["active_config"]]

        Log.info('BOT', f"Using active config {self._active['name']}")
        Log.info('BOT', f"Using {len(self._config['pairs'])} coin pairs.")

        self._client = await AsyncClient.create(api_key=self._active["key"], api_secret=self._active["secret"])
        self._socket_manager = BinanceSocketManager(self._client) # user_timeout is now 5 minutes (5 * 60)

        status = await self._client.get_system_status()
        Log.info('BOT', f"System status: {status['msg']}")

        self._coin_manager = CoinManager(self, self._config['pairs'])
        self._order_manager = OrderManager(self)
        self._wallet = Wallet(self)

        Log.info('BOT', f"Total usable ${(await self._wallet.get_money()):.2f} in spot wallet.")

        # self.tasks = self._coin_manager.init()
        self.tasks.append(self._coin_manager.init_multiplex())

        # keep the main event loop active
        while self._running:
            await asyncio.sleep(0.01)
        # close our connection cleanly
        await self._client.close_connection()

    def shutdown(self, signal, stack_frame):
        Log.info('BOT', 'Application exitted.')

        for task in self.tasks:
            task.cancel()

        self._running = False
