class Wallet:
    def __init__(self, bot):
        self.bot = bot

    @property
    def money(self):
        return self._money

    async def transfer_to_isolated(self, symbol, symbol_pair, amount):
        t = self.bot.client.transfer_spot_to_isolated_margin(asset=symbol, symbol=symbol_pair, amount=amount)

        self.bot.log.verbose('WALLET', f'Transfer {amount} {symbol} to isolated')

        await self.update_money()

        return t

    async def transfer_to_spot(self, symbol, symbol_pair, amount):
        t = await self.bot.client.transfer_isolated_margin_to_spot(asset=symbol, symbol=symbol_pair, amount=amount)

        self.bot.log.verbose('WALLET', f'Transfer {amount} {symbol} to spot')

        await self.update_money()

        return t

    async def update_money(self):
        res = await self.bot.client.get_asset_balance('USDT')

        self._money = float(res['free'])

        self.bot.log.verbose('WALLET', f'Updated money in wallet, new wallet total: {self._money}')

        return self._money
