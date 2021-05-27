import asyncio
from binance import AsyncClient, BinanceSocketManager
from time import sleep
from src.util.logger import Log
from src.util.util import util
from .coin_manager import CoinManager
from .order_manager import OrderManager
from .wallet import Wallet

class CryptoBot:
    def __init__(self):
        self._running = True

        self.tasks = []

    @property
    def bm(self) -> BinanceSocketManager:
        return self._socket_manager

    @property
    def client(self) -> AsyncClient:
        return self._client

    @property
    def indicators(self):
        return self._indicators

    @property
    def log(self) -> Log:
        return Log

    @property
    def order_manager(self) -> OrderManager:
        return self._order_manager

    @property
    def symbol_pairs(self):
        return self._symbol_pairs

    @property
    def user(self) -> dict:
        return self._user

    @property
    def wallet(self) -> Wallet:
        return self._wallet
    
    @property
    def mongo(self):
        return self._mongo

    async def start(self, config, symbol_pairs, indicators, mongo):
        self._indicators = {}
        for indicator in indicators:
            self._indicators[indicator['name']] = indicator

        self._symbol_pairs = symbol_pairs
        self._user = config
        self._mongo = mongo

        Log.info('BOT', f"Using active config {self._user['name']}")
        Log.info('BOT', f"Using {len(list(self._symbol_pairs.clone()))} coin pairs.")

        self._client = await AsyncClient.create(api_key=self._user["api_keys"]["key"], api_secret=self._user["api_keys"]["secret"])
        self._socket_manager = BinanceSocketManager(self._client) # user_timeout is now 5 minutes (5 * 60)

        status = await self._client.get_system_status()
        if status['status'] == 0:
            Log.info('BOT', f"Binance system status: {status['msg']}")
        else:
            Log.warning('BOT', f"Binance system status: {status['msg']}")

        self._coin_manager = CoinManager(self, self._symbol_pairs)
        self._order_manager = OrderManager(self)
        self._wallet = Wallet(self)

        await self._wallet.update_money('USDT')
        await self._wallet.update_money('EUR')
        # Log.info('BOT', f"Total usable {(await self._wallet.update_money('USDT')):.2f} USDT in spot wallet.")
        # Log.info('BOT', f"Total usable {(await self._wallet.update_money('EUR')):.2f} EURO in spot wallet.")

        self.tasks = await self._coin_manager.init()

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
