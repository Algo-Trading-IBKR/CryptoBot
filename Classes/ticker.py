class Ticker:
    def __init__(self, ticker):
        self.ticker = ticker
        self.highs = []
        self.lows = []
        self.volumes = []
        self.closes = []
        self.has_position = False


    def get_highs(self):
        print(self.highs)