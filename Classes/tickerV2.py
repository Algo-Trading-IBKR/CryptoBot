from datetime import datetime

class Ticker:
    def __init__(self, ticker,log_file):
        self.ticker = ticker
        self.money = 100
        self.highs = []
        self.lows = []
        self.volumes = []
        self.closes = []

        self.log = log_file
        self.log_file = open(f"{log_file}/{ticker}.txt","w+")
        self.log_file.close()

        self.has_position = False
        self.average_price = 0 
        self.stop_loss = 0
        self.take_profit = 0
        self.amount = 0

    def log_buy(self, buy_price, ticker, amount, money):
        now = datetime.now()
        day = datetime.today()
        day = day.strftime("%d %b %Y")
        now = now.strftime("%H:%M:%S")
        self.log_file = open(f"{self.log}/{ticker}.txt", "a+")
        self.log_file.write(f"{day} - {now} | Bought {amount:.3f} {ticker} with {money} dollar for {buy_price} dollar per unit. \n")
        self.log_file.close()

    def log_sell(self, profit, price, ticker, amount, money):
        now = datetime.now()
        day = datetime.today()
        now = now.strftime("%H:%M:%S")
        day = day.strftime("%d %b %Y")

        self.log_file = open(f"{self.log}/{ticker}.txt", "a+")
        if profit:
            self.log_file.write(f"{day} - {now} | PROFIT, sold {amount} {ticker} for {price} dollar per unit. Money left {money} dollar\n")
            self.log_file.close()
        else:
            self.log_file.write(f"{day} - {now} | LOSS, sold {amount} {ticker} for {price} dollar per unit. Money left {money} dollar\n")
            self.log_file.close()