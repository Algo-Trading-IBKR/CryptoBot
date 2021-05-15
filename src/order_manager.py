from decimal import Decimal
from .order_book import OrderBook

class OrderManager():
    def __init__(self, bot):
        self.bot = bot

        self.order_book = OrderBook()

    async def cancel_order(self, coin, side):
        order_id = self.order_book.get_order_for_symbol(coin.symbol_pair, side)
        if order_id == None:
            self.bot.log.warning('ORDER_MANAGER', f'Attempted {side} order cancel for {coin.symbol_pair} but got None')
            return

        self.bot.log.info('ORDER_MANAGER', f'Cancelled order for {coin.symbol_pair} with ID {order_id}')

        result = await self.bot.client.cancel_margin_order(symbol=coin.symbol_pair, order_id=order_id, isIsolated="TRUE")
        self.bot.log.verbose('ORDER_MANAGER', f'Order Cancelled: {result}')

    async def get_low(self, symbol):
        data = await self.bot.client.get_ticker(symbol=symbol)

        return float(data['lowPrice'])

    def has_order_id(self, symbol_pair, order_id):
        return self.order_book.has_order_id(symbol_pair, order_id)

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

        self.bot.log.info('ORDER_MANAGER', f'[{order["status"]} | {order_type}] {order["side"]} order for {coin.symbol_pair} (id: {order['orderId']}), quantity {str(quantity)[:-10]} at {price} USDT with effect {side_effect}')

        if order['side'] == 'SELL':
            self.order_book.set_order_for_symbol(coin.symbol_pair, order['side'], order['orderId'])
            return False
        if order['status'] == 'FILLED' and order['side'] == 'BUY':
            coin.has_open_order = False
            return True
        if order['side'] == 'BUY':
            self.order_book.set_order_for_symbol(coin.symbol_pair, order['side'], order['orderId'])
            coin.has_open_order = True
            return False
