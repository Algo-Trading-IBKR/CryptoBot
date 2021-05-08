import threading

class Coin(threading.Thread):
    def __init__(self, bot, symbol_pair : str):
        threading.Thread.__init__(self)

        self.bot = bot
        self.symbol_pair = symbol_pair

    def run(self):
        pass
