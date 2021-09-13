import asyncio
from binance import AsyncClient, BinanceSocketManager
from time import time
from concurrent.futures import CancelledError
import traceback
from time import sleep
from src.util.logger import Log
from src.util.util import util
from src.util.coin_updater import updater
from .coin_manager import CoinManager
from .order_manager import OrderManager
from .wallet import Wallet
from bson.objectid import ObjectId
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

    async def start(self, config, mongo):
        self._api_url = os.environ.get('API_URL')

        self._user = config
        self._mongo = mongo

        self._indicators = {}
        for indicator in self._user['strategy']['indicators']:
            self._indicators[indicator['name']] = indicator

        Log.info('BOT', f"Using active config {self._user['name']}")

        self._client = await AsyncClient.create(api_key=self._user["api_keys"]["key"], api_secret=self._user["api_keys"]["secret"])
        self._socket_manager = BinanceSocketManager(self._client) # user_timeout is now 5 minutes (5 * 60)

        await self.get_exchange_info()

        await updater(self)

        # NEW VERSION #
        #####################################################
        self._symbol_pair_ids = self._user['coins']['inactive']
        self._symbol_pairs = mongo.cryptobot.symbol_pairs.find({ "active": True })
        self.active_symbol_pairs = [coin for coin in self._symbol_pairs if str(coin["_id"]) not in self._symbol_pair_ids]
        self.inactive_symbol_pairs = [coin for coin in self._symbol_pairs if str(coin["_id"]) in self._symbol_pair_ids]
        
        Log.info('BOT', f"Using {len(self.active_symbol_pairs)+len(self.inactive_symbol_pairs)} coin pairs.")
        ####################################################

        self._coin_manager = CoinManager(self, self.active_symbol_pairs, self.inactive_symbol_pairs)
        self._order_manager = OrderManager(self)
        self._wallet = Wallet(self)

        await self._wallet.update_money('USDT')
        await self._wallet.update_money('EUR')

        self.tasks.append(asyncio.create_task(self.user_check()))

        self.tasks.append(await self._coin_manager.init())
        
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


    ### ON STARTUP: coins in active and inactive list stay there untill after startup, this might need to be updated 
    async def user_check(self):
        self._running = True
        Log.verbose('BOT', f'Starting perpetual user check')
        while self._running:
            try:
                await asyncio.sleep(5)
                userObject = self._mongo.cryptobot.users.find_one({ "active": True, "_id": ObjectId(self._user["_id"]) })
                if userObject["coins"] != self._user["coins"]:
                    deactivatedPairs = []
                    for coinId in userObject["coins"]["inactive"]:
                        coin = self._mongo.cryptobot.symbol_pairs.find_one({ "active": True, "_id": ObjectId(coinId) })
                        deactivatedPairs.append(coin["trade_symbol"]+coin["currency_symbol"])
                        if coin and coin["trade_symbol"]+coin["currency_symbol"] in self._coin_manager._coins:
                            self._coin_manager._coins[coin["trade_symbol"]+coin["currency_symbol"]].initialised = False
                            self._coin_manager._coins[coin["trade_symbol"]+coin["currency_symbol"]].active = False
                            Log.verbose('BOT', f"Coin {coin['trade_symbol']}/{coin['currency_symbol']} disabled")

                    for coin in self._coin_manager._coins.values():
                        if coin.active == False and coin.symbol_pair not in deactivatedPairs:
                            coin.active = True
                            asyncio.create_task(coin.init())
                            Log.verbose('BOT', f"Coin {coin.symbol_pair} enabled")

                    self._user = userObject
                elif userObject != self._user:
                    self._user = userObject
                
            except (CancelledError,Exception) as e:
                if isinstance(e, CancelledError):
                    self._running = False
                Log.error('BOT', f'Error occured:\n{traceback.format_exc()}')

    def shutdown(self, signal, stack_frame):
        Log.info('BOT', 'Application exitted.')

        for task in self.tasks:
            task.cancel()

        self._running = False
