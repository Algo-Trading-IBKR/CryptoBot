import asyncio
from binance import AsyncClient, BinanceSocketManager
from time import sleep
from src.util.logger import Log
from src.util.util import util
from .coin_manager import CoinManager
from .order_manager import OrderManager
from .wallet import Wallet
import os
import requests
import sys
# import json

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

    @property
    def api_url(self):
        return self._api_url

    @property
    def exchange_info(self):
        return self._exchange_info

    async def start(self, config, symbol_pairs, mongo):
        self._api_url = os.environ.get('API_URL')

        self._symbol_pairs = symbol_pairs
        self._user = config
        self._mongo = mongo

        self._indicators = {}
        for indicator in self._user['strategy']['indicators']:
            self._indicators[indicator['name']] = indicator

        Log.info('BOT', f"Using active config {self._user['name']}")
        Log.info('BOT', f"Using {len(list(self._symbol_pairs.clone()))} coin pairs.")

        self._client = await AsyncClient.create(api_key=self._user["api_keys"]["key"], api_secret=self._user["api_keys"]["secret"])
        self._socket_manager = BinanceSocketManager(self._client) # user_timeout is now 5 minutes (5 * 60)

        await self.get_exchange_info()

        # remove if user count increases too much, could cause api ban
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

        user_count = self.mongo.cryptobot.users.count_documents({"active": True})
        self.tasks = await self._coin_manager.init(user_count)

        # keep the main event loop active
        while self._running:
            await asyncio.sleep(0.1)
            if str(await self._client.ping()) != '{}':
                sys.exit()
        # close our connection cleanly
        await self._client.close_connection()
    
    # if this fails try restarting REST API
    async def get_exchange_info(self):
        params = {'api_secret': self.user["api_keys"]["secret"]}
        url = self.api_url+"/binance/exchange_info"
        info = requests.get(url=url, params=params)
        self._exchange_info = info.json()

    def shutdown(self, signal, stack_frame):
        Log.info('BOT', 'Application exitted.')

        for task in self.tasks:
            task.cancel()

        self._running = False
