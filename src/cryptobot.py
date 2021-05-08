import asyncio
from binance import AsyncClient
from src.util.logger import Log
from src.util.util import load_json
from .coin import Coin
from .order_manager import OrderManager
from .wallet import Wallet

class CryptoBot:
    def __init__(self):
        self._config = load_json('./configs/config.json')

    @property
    def client(self):
        return self._client

    @property
    def config(self):
        return self._config

    def load_coins(self):
        pass

    async def start(self):
        self._active = self._config["configs"][self._config["active_config"]]

        Log.info('BOT', f"Using active config {self._active['name']}")
        Log.info('BOT', f"Using {len(self._config['pairs'])} coin pairs.")

        self._client = await AsyncClient.create(api_key=self._active["key"], api_secret=self._active["secret"])

        status = await self._client.get_system_status()
        Log.info('BOT', f"System status: {status['msg']}")

        self._coins = [Coin(self, symbol_pair) for symbol_pair in self._config["pairs"]]
        self._order_manager = OrderManager(self)
        self._wallet = Wallet(self)

        for coin in self._coins:
            coin.start()

        await self._client.close_connection()

    async def shutdown(self):
        # gracefull shutdown, close positionts etc
        await self._client.close_connection()
