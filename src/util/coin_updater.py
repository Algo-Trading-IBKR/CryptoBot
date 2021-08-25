from binance import *
from random import shuffle
import requests
import json

unwanted = ["EUR", "GBP", "AED", "ARS", "AUD", "BRL", "CAD", "CHF", "CZK", "DKK", "GHS", "HKD", "HUF", "JPY", "KES", "KZT", "KES", "KZT", "MXN", "NGN", "NOK", "NZD", "PEN", "PLN", "RUB", "SEK", "TRY", "UAH", "UGX", "VND", "ZAR", "PAX", "SUSDT", "BUSD", "TUSD", "USDC", "USDSB"]

async def updater(bot):
    API_KEY = bot.user["api_keys"]["key"]
    SECRET_KEY = bot.user["api_keys"]["secret"]
    URL = bot.api_url + "/coin"
        
    twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=SECRET_KEY)
    twm.start()
    res = await bot.client.get_exchange_info()
    symbols = res["symbols"]
    shuffle(symbols)
    for symbol in symbols:
        if str(symbol["symbol"][:-4]) not in unwanted:
            s = symbol["symbol"]
            if s[-4:] == "USDT" or s[-3:] == "EUR":
                if s[-4:] == "USDT":
                    currency = "USDT"
                    coin = s[:-4]
                elif s[-3:] == "EUR":
                    currency = "EUR"
                    coin = s[:-3]
                else:
                    pass
                if len(coin) >= 4 and (coin[-4:] == "BULL" or coin[-4:] == "BEAR" or coin[-4:] == "DOWN" or coin[-2:] == "UP"):
                    pass
                else:
                    myobj = { "active": True, "trade_symbol": coin, "currency_symbol": currency, "api_secret": SECRET_KEY}
                    myobj = json.dumps(myobj)
                    x = requests.post(url = URL, data = myobj)
    bot.log.info('COIN UPDATER', "updated coins in database")
