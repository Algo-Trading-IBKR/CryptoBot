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
    influx_bucket = os.environ.get('INFLUX_BUCKET')
    influx_org = os.environ.get('INFLUX_ORG')
    influx_token = os.environ.get('INFLUX_TOKEN')
    influx_url = os.environ.get('INFLUX_URL')

    influx_config = [influx_bucket, influx_org, influx_token, influx_url]

    client = MongoClient(mongo_connect_url)

    indicators = client.cryptobot.indicators.find({})
    symbol_pairs = client.cryptobot.symbol_pairs.find({ "active": True })
    user_config = client.cryptobot.users.find_one({ "active": True, "name": active_config })

    cryptobot.log.set_log_group(active_config)

    if user_config == None:
        return cryptobot.log.info('MAIN', f'User config "{active_config}" is disabled')

    await cryptobot.start(user_config, symbol_pairs, indicators, influx_config)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


    # self.bucket = config
    # self.org = config
    # self.token = config
    # self.url = config
