buy = 100
stop_loss = 2
take_profit = 3


limit_loss = buy - (buy * (stop_loss/100))
limit_profit = buy *(1 + (take_profit/100))
print((limit_profit))