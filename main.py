import asyncio
import os
import signal
from pymongo import MongoClient
from src.cryptobot import CryptoBot

cryptobot = CryptoBot()
cryptobot.log.log_level = 'VERB' # VERB/INFO/WARN/ERR/CRIT

signal.signal(signal.SIGINT, cryptobot.shutdown)
signal.signal(signal.SIGTERM, cryptobot.shutdown)

async def main():
    active_config = os.environ.get('ACTIVE_CONFIG')
    mongo_connect_url = os.environ.get('MONGODB_URL')

    client = MongoClient(mongo_connect_url)

    indicators = client.cryptobot.indicators.find({})
    symbol_pairs = client.cryptobot.symbol_pairs.find({})
    user_config = client.cryptobot.users.find_one({ "name": active_config })

    await cryptobot.start(user_config, symbol_pairs, indicators)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
