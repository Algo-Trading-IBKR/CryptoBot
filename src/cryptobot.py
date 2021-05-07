import asyncio
from binance import AsyncClient
from src.util.logger import Logger
from src.util.util import load_json

class CryptoBot:
    def __init__(self):
        self._config = load_json('./configs/config.json')

    @property
    def config(self):
        return self._config

    def load_coins(self):
        pass

    async def start(self):
        self._active = self._config["configs"][self._config["active_config"]]

        Logger.info('BOT', f"Using active config {self._active['name']}")
        Logger.info('BOT', f"Using {len(self._config['pairs'])} coin pairs.")

        self._client = await AsyncClient.create(self._active["key"], self._active["secret"])

    def shutdown(self):
        # gracefull shutdown, close positionts etc

        pass
