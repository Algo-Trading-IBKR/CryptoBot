class Wallet:
    def __init__(self, bot):
        self.bot = bot

    async def get_money(self):
        res = await self.bot.client.get_asset_balance('USDT')

        return float(res['free'])
