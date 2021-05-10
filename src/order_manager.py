from decimal import Decimal

class OrderManager():
    def __init__(self, bot):
        self.bot = bot

        self.order_book = {}

    async def cancel_order(self, coin):
        if coin.symbol_pair not in self.order_book:
            return
        order_id = self.order_book[coin.symbol_pair]

        result = self.bot.client.cancel_margin_order(symbol=coin.symbol_pair, order_id=order_id)
        self.bot.log.verbose('ORDER_MANAGER', f'Order Cancelled: {result}')

    async def get_low(self, symbol):
        data = await self.bot.client.get_ticker(symbol=symbol)

        return float(data['lowPrice'])

    def repay_margin_loan(self, coin):
        pass

    async def send_order(self, coin, side : str, quantity : Decimal, price : float, order_type : str, isolated : bool, side_effect : str, time_in_force : str) -> bool:
        order = await self.bot.client.create_margin_order(
            side=side,
            quantity=quantity,
            symbol=coin.symbol_pair,
            price=price,
            type=order_type,
            isIsolated=isolated,
            sideEffectType=side_effect,
            timeInForce=time_in_force
        )

        await self.bot.wallet.update_money()

        if order['side'] == 'SELL':
            self.order_book[coin.symbol_pair] = order['orderId']
            return False
        if order['status'] == 'FILLED' and order['side'] == 'BUY':
            coin.has_open_order = False
            return True
        if order['side'] == 'BUY':
            self.order_book[coin.symbol_pair] = order['orderId']
            coin.has_open_order = True
            return False
