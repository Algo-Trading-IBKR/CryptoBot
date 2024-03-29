from decimal import Decimal
from .order_book import OrderBook
from datetime import datetime
import uuid

class OrderManager():
    def __init__(self, bot):
        self.bot = bot

        self.order_book = OrderBook(bot)

    async def cancel_order(self, coin, side):
        order_id = self.order_book.get_order_for_symbol(coin.symbol_pair, side)
        if order_id == None:
            self.bot.log.warning('ORDER_MANAGER', f'Attempted {side} order cancel for {coin.symbol_pair} but got None')
            return False

        self.bot.log.info('ORDER_MANAGER', f'Cancelled order for {coin.symbol_pair}')

        try:
            result = await self.bot.client.cancel_order(symbol=coin.symbol_pair, orderId=order_id)
            self.bot.log.info('ORDER_MANAGER', f'Order Cancelled: {result}')
            try:
                old_order = self.bot.mongo.cryptobot.orders.find_one({"orderId": order_id})
                if old_order:
                    result.update({"user_id": coin.bot.user["_id"]})
                    result.update({"datetime": datetime.now()})
                    self.bot.mongo.cryptobot.orders.replace_one(old_order, result, upsert=True)
            except Exception as e:
                self.bot.log.warning('ORDER_MANAGER', f'update mongo trade failed: {str(e)}')
            return True
        except Exception as e:
            self.bot.log.warning('ORDER_MANAGER', f'Failed to cancel order: {e}')
            return False


    # async def get_low(self, symbol):
    #     data = await self.bot.client.get_ticker(symbol=symbol)
    #     return float(data['lowPrice'])

    def has_order_id(self, symbol_pair, order_id):
        return self.order_book.has_order_id(symbol_pair, order_id)

    async def send_order(self, coin, side : str, quantity : Decimal, price : float, order_type : str, time_in_force : str, piramidding : bool = False) -> bool:
        order = await self.bot.client.create_order(
            symbol=coin.symbol_pair,
            side=side,
            type=order_type,
            timeInForce=time_in_force,
            quantity=f"{round(quantity,coin.precision)}", # -1 to prevent issues, sometimes precision is wrong
            price=price,
            newClientOrderId="CryptoBot"+str(uuid.uuid4().hex)[:25] # max 36 characters
        )

        order.update({"user_id": coin.bot.user["_id"]})
        order.update({"datetime": datetime.now()})
        coin.bot.mongo.cryptobot.orders.insert_one(order)

        await self.bot.wallet.update_money(coin.currency) # mogelijks overbodig

        self.bot.log.info('ORDER_MANAGER', f'[{order["status"]} | {order_type}] {order["side"]} order for {coin.symbol_pair}, quantity {str(quantity)[:-30]} at {price} {coin.currency}')

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
