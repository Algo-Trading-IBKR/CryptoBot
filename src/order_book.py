sides = ['BUY', 'SELL']

class OrderBook:
    def __init__(self, bot):
        self._buy = {}
        self._sell = {}
        self.bot = bot

    def get_order_for_symbol(self, symbol_pair : str, side : str) -> int:
        if side not in sides:
            return None
        return self._sell[symbol_pair] if side == 'SELL' else self._buy[symbol_pair]

    def has_order_id(self, symbol_pair : str, order_id):
        return (symbol_pair in self._buy and self._buy[symbol_pair] == order_id) or (symbol_pair in self._sell and self._sell[symbol_pair] == order_id)

    def set_order_for_symbol(self, symbol_pair : str, side, order_id) -> None:
        if side == 'SELL':
            self._sell[symbol_pair] = order_id
        elif side == 'BUY':
            self._buy[symbol_pair] = order_id
        else:
            # raise ValueError('Invalid/unknown side given for set_order_for_symbol')
            self.bot.log.error('ORDER_BOOK', f'Invalid/unknown side "{side}" given for set_order_for_symbol')

    def symbol_in_orderbook(self, symbol_pair : str, side : str) -> bool:
        if side not in sides:
            return False
        return symbol_pair in self._sell if side == 'SELL' else symbol_pair in self._buy
