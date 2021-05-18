class Wallet:
    def __init__(self, bot):
        self.bot = bot

    @property
    def money(self):
        return self._money

    async def update_money(self):
        res = await self.bot.client.get_asset_balance('USDT')

        self._money = float(res['free'])

        self.bot.log.info('WALLET', f'Updated money in wallet, new wallet total: {self._money}')

        return self._money
