class Wallet:
    def __init__(self, bot):
        self.bot = bot

    @property
    def money(self):
        return self._money

    async def update_money(self, asset : str ):
        res = await self.bot.client.get_asset_balance(asset)

        self._money = float(res['free'])

        self.bot.log.info('WALLET', f'Updated money in wallet, new wallet total: {self._money} {asset}')

        return self._money
