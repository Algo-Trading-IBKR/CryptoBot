import asyncio
import os
import signal
from src.cryptobot import CryptoBot

cryptobot = CryptoBot()
cryptobot.log.log_level = 'VERB' # VERB/INFO/WARN/ERR/CRIT

signal.signal(signal.SIGINT, cryptobot.shutdown)
signal.signal(signal.SIGTERM, cryptobot.shutdown)

async def main():
    await cryptobot.start(os.environ.get('ACTIVE_CONFIG'))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
