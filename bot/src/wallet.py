from datetime import datetime, timedelta

class Wallet:
    def __init__(self, bot):
        self.bot = bot
        self._money = {}
        self._last_update = {}

    @property
    def money(self):
        return self._money
    
    @property
    def last_update(self):
        return self._last_update

    async def update_money(self, asset : str ):
        if not asset in self._last_update:
            self.bot.log.verbose('WALLET', f'new asset {asset}')
            self._last_update[asset] = datetime.now()
            res = await self.bot.client.get_asset_balance(asset)
            self._money[asset] = float(res['free'])
            self.bot.log.info('WALLET', f'balance update, new wallet total: {self._money[asset]} {asset}')
            return self._money[asset]

        if datetime.now() < self._last_update[asset] + timedelta(seconds=10):
            return self._money[asset]

        self._last_update[asset] = datetime.now()
        res = await self.bot.client.get_asset_balance(asset)
        self._money[asset] = float(res['free'])
        self.bot.log.info('WALLET', f'balance update, new wallet total: {self._money[asset]} {asset}')
        return self._money[asset]
