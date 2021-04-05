from datetime import datetime
import os


class Ticker:
    def __init__(self, ticker,log_file):
        self.ticker = ticker
        self.money = 100 # not used for live version
        self.highs = []
        self.lows = []
        self.volumes = []
        self.closes = []

        self.log = log_file
        if not os.path.exists(f'{log_file}'):
            os.makedirs(log_file)
        self.log_file = open(f"{log_file}/{ticker}.txt","w+")
        self.log_file.close()

        self.has_position = False # get when reboot
        self.average_price = 0 # get when reboot
        self.stop_loss = 0 # get when reboot
        self.take_profit = 0 
        self.amount = 0 # get out of api , get when reboot

        self.precision = 0
        
        # margin
        self.margin_ratio = 1
        self.liquidation_price = 0 #get in the start

        self.TP_order_ID = 0 #get when reboot
        


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