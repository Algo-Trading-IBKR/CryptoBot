class Wallet:
    def __init__(self, bot):
        self.bot = bot
        self._money = {}

    @property
    def money(self):
        return self._money

    async def update_money(self, asset : str ):
        res = await self.bot.client.get_asset_balance(asset)

        self._money[asset] = float(res['free'])

        self.bot.log.info('WALLET', f'balance update, new wallet total: {self._money[asset]} {asset}')

        return self._money[asset]
