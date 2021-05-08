import asyncio
import signal
from src.cryptobot import CryptoBot

cryptobot = CryptoBot()

signal.signal(signal.SIGINT, cryptobot.shutdown)
signal.signal(signal.SIGTERM, cryptobot.shutdown)

async def main():
    await cryptobot.start()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
