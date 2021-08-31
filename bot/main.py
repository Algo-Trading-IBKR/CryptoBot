import asyncio
import os
import signal
from pymongo import MongoClient
from src.cryptobot import CryptoBot
from bson.objectid import ObjectId

cryptobot = CryptoBot()
cryptobot.log.log_level = 'INFO' # VERB/INFO/WARN/ERR/CRIT

signal.signal(signal.SIGINT, cryptobot.shutdown)
signal.signal(signal.SIGTERM, cryptobot.shutdown)

async def main():
    try:
        active_config = os.environ.get('ACTIVE_CONFIG')
        mongo_connect_url = os.environ.get('MONGODB_URL')

        Mongo = MongoClient(mongo_connect_url)

        cryptobot.log.set_log_group(active_config)

        # symbol_pairs = Mongo.cryptobot.symbol_pairs.find({ "active": True })
        
        user_id = active_config.split('_')[1]
        user_config = Mongo.cryptobot.users.find_one({ "active": True, "_id": ObjectId(user_id) })
        
        if user_config == None:
            return cryptobot.log.info('MAIN', f'User config "{user_id}" is disabled')

        await cryptobot.start(user_config, Mongo)
    except Exception as e:
        print(str(e))

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        print(str(e))

