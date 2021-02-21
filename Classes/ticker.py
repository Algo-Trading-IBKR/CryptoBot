class Ticker:
    def __init__(self, ticker):
        self.ticker = ticker

        self.highs = []
        self.lows = []
        self.volumes = []
        self.closes = []

        self.has_position = False
        self.buy_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.order_succeeded = False

    def get_highs(self):
        print(self.highs)



