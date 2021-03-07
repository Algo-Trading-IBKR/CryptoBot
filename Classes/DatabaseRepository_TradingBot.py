import pymongo
import datetime as dt

class Database():
    # client = pymongo.MongoClient("mongodb://TradingBot:mT8qdJ5NGt!qGrqOzchKH8w9Zw!U4HDzg94RgYt1SWlfàDU7@localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false&authSource=admin")
    # client = pymongo.MongoClient("mongodb://Joren:JorenvanGoethem@localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false&authSource=admin")
    client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")


    db = client["TradingBot"]

    symbols = db["Symbols"]
    rawdata = db["RawData"]
    strategydata = db["StrategyData"]
    order_log = db["OrderLog"]
    execution_log = db["ExecutionLog"]
    commission_log = db["CommisionLog"]
    account_info = db["AccountInfo"]
    error_log = db["ErrorLog"]
    
    #region Symbols
    @staticmethod
    def insert_symbol(symbol: str, datetime: dt.datetime, shares: float, averagePrice: float, realizedpnl: float, unrealizedpnl: float):
        # data = {"Symbol": symbol, "DateTime": datetime, "Shares": shares, "AveragePrice": averagePrice,"RealizedPnL": realizedpnl, "UnrealizedPnL": unrealizedpnl, "LatestUpdate": dt.datetime.now() }
        data = {"Symbol": symbol, "DateTime": datetime, "Shares": shares, "AveragePrice": averagePrice, "UnrealizedPnL": unrealizedpnl }
        insert = Database.symbols.insert_one(data)
      
    @staticmethod
    def update_symbol(symbol: str, datetime: dt.datetime, shares: float, averagePrice: float, realizedpnl: float, unrealizedpnl: float):
        data = {"Symbol": symbol}
        # newdata = {"$set": {"Symbol": symbol, "DateTime": datetime, "Shares": shares, "AveragePrice": averagePrice,"RealizedPnL": realizedpnl, "UnrealizedPnL": unrealizedpnl, "LatestUpdate": dt.datetime.now() } }
        newdata = {"$set": {"Symbol": symbol, "DateTime": datetime, "Shares": shares, "AveragePrice": averagePrice, "UnrealizedPnL": unrealizedpnl } }
        Database.symbols.update_one(data, newdata, upsert=True)
    
    @staticmethod
    def read_symbol(symbol: str):
        query = {"Symbol": symbol}
        item = Database.symbols.find_one(query)
        return item

    @staticmethod
    def read_all_symbols():
        items = Database.symbols.find()
        return items

    @staticmethod
    def delete_symbol(symbol: str):
        query = {"Symbol": symbol}
        item = Database.symbols.delete_one(query)

    @staticmethod
    def delete_all_symbols():
        items = Database.symbols.delete_many({})
    #endregion
    
    #region Raw Data
    @staticmethod
    def insert_raw_data(symbol: str, datetime: dt.datetime, price: float):
        data = {"Symbol": symbol, "DateTime": datetime, "Price": price}
        insert = Database.rawdata.insert_one(data)
    
    @staticmethod
    def update_raw_data(symbol: str, datetime: dt.datetime, price: float):
        data = {"Symbol": symbol, "DateTime": datetime}
        newdata = {"$set": {"Symbol": symbol, "DateTime": datetime, "Price": price} }
        Database.rawdata.find_one_and_update(data, newdata, upsert=True)  
    
    @staticmethod
    def read_raw_data(symbol: str, amount: int = 3000):
        query = {"Symbol": symbol}
        item = Database.rawdata.find(query).sort("DateTime", -1).limit(amount)
        return item
    
    @staticmethod
    def read_latest_raw_data(symbol: str):
        query = {"Symbol": symbol}
        item = Database.rawdata.find_one(query)
        return item

    @staticmethod
    def read_raw_data_by_time(symbol: str, datetime: dt.datetime):
        query = {"Symbol": symbol, "DateTime": datetime}
        item = Database.rawdata.find_one(query)
        return item

    @staticmethod
    def read_all_raw_data(symbol: str):
        query = {"Symbol": symbol}
        items = Database.rawdata.find(query)
        return items

    @staticmethod
    def delete_raw_data(symbol: str):
        query = {"Symbol": symbol}
        item = Database.rawdata.delete_one(query)

    @staticmethod
    def delete_all_raw_data():
        items = Database.rawdata.delete_many({})
    #endregion

    #region Strategy Data
    @staticmethod
    def insert_strategy_data(symbol: str, datetime: dt.datetime, price: float):
        data = {"Symbol": symbol, "DateTime": datetime, "Price": price}
        insert = Database.strategydata.insert_one(data)
        
    @staticmethod
    def update_strategy_data(symbol: str, datetime: dt.datetime, price: float):
        data = {"Symbol": symbol, "DateTime": datetime}
        newdata = {"$set": {"Symbol": symbol, "DateTime": datetime, "Price": price} }
        Database.strategydata.update_one(data, newdata, upsert=True)
    
    @staticmethod
    def read_strategy_data(symbol: str, amount: int = 30): #27 should be fine
        query = {"Symbol": symbol}
        items = Database.strategydata.find(query).sort("DateTime", -1).limit(amount)
        return items

    @staticmethod
    def read_strategy_data_by_time(symbol: str, datetime: dt.datetime):
        query = {"Symbol": symbol, "DateTime": datetime}
        item = Database.strategydata.find_one(query)
        return item

    @staticmethod
    def read_all_strategy_data(symbol: str):
        query = {"Symbol": symbol}
        items = Database.strategydata.find(query)
        return items

    @staticmethod
    def delete_one_strategy_data(symbol: str):
        query = {"Symbol": symbol}
        item = Database.strategydata.delete_one(query)

    @staticmethod
    def delete_strategy_data(symbol: str):
        query = {"Symbol": symbol}
        item = Database.strategydata.delete_many(query)

    @staticmethod
    def delete_all_strategy_data():
        items = Database.strategydata.delete_many({})
    #endregion

    #region Order Logs
    @staticmethod
    def insert_order_log(symbol: str, datetime: dt.datetime, ordertype: str, instruction: str, orderid: int, currentprice: float):
        data = {"Symbol": symbol, "DateTime": datetime, "OrderType": ordertype, "Instruction": instruction, "OrderId": orderid, "CurrentPrice": currentprice, "Filled": False, "Canceled": False}
        insert = Database.order_log.insert_one(data)
    
    @staticmethod
    def fill_order(symbol: str, orderid: int):
        data = {"Symbol": symbol, "OrderId": orderid}
        newdata = {"$set": {"Filled": True} }
        Database.order_log.update_one(data, newdata)
    
    @staticmethod
    def cancel_order(symbol: str, orderid: int):
        data = {"Symbol": symbol, "OrderId": orderid}
        newdata = {"$set": {"Canceled": True} }
        Database.order_log.update_one(data, newdata)

    @staticmethod
    def get_unfinished_orders():
        query = {"Filled": False, "Canceled": False}
        items = Database.order_log.find(query)
        return items

    @staticmethod
    def get_unfinished_sell_orders_for_symbol(symbol:str):
        query = {"Symbol": symbol, "Instruction": "SELL", "Filled": False, "Canceled": False}
        items = Database.order_log.find(query)
        return items

    @staticmethod
    def get_unfinished_buy_orders():
        query = {"Instruction": "BUY", "Filled": False, "Canceled": False}
        items = Database.order_log.find(query)
        return items
    
    
    @staticmethod
    def cancel_orders_for_symbol(symbol: str):
        query = {"Symbol": symbol, "Filled": False, "Canceled": False}
        items = Database.order_log.find(query)
        return items

    @staticmethod
    def read_order_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.order_log.find_one(query)
        return item
    
    @staticmethod
    def read_order_log_by_id(symbol: str, orderid: int):
        query = {"Symbol": symbol, "OrderId": orderid}
        item = Database.order_log.find_one(query)
        return item

    @staticmethod
    def read_order_logs(symbol: str):
        query = {"Symbol": symbol}
        item = Database.order_log.find(query)
        return item

    @staticmethod
    def read_all_order_logs():
        items = Database.order_log.find()
        return items

    @staticmethod
    def delete_order_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.order_log.delete_one(query)

    @staticmethod
    def delete_order_logs(symbol: str):
        query = {"Symbol": symbol}
        items = Database.order_log.delete_many(query)

    @staticmethod
    def delete_all_order_logs():
        item = Database.order_log.delete_many({})
    #endregion

    #region Execution Logs
    @staticmethod # Insert New Execution Log
    def insert_execution_log(symbol: str, datetime: dt.datetime, shares: float, averagePrice: float, execid: str, orderid: int):
        order = Database.read_order_log_by_id(symbol, orderid)
        Database.fill_order(symbol, orderid)
        if order != None:
            instruction = order["Instruction"]
            ordertype = order["OrderType"]
        
            data = {"Symbol": symbol, "DateTime": datetime, "Shares": shares, "AveragePrice": averagePrice, "OrderType": ordertype, "Instruction": instruction,"ExecId": execid}
            insert = Database.execution_log.insert_one(data)
    
    @staticmethod # Read Latest Execution Log of symbol
    def read_execution_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.execution_log.find_one(query)
        return item

    @staticmethod # Read Latest Execution Log of symbol
    def read_execution_log_by_id(execid: str):
        query = {"ExecId": execid}
        item = Database.execution_log.find_one(query)
        return item

    @staticmethod # Read All Execution Logs of symbol
    def read_execution_logs(symbol: str):
        query = {"Symbol": symbol}
        items = Database.execution_log.find(query)
        return items

    @staticmethod # Read ALL Execution Logs
    def read_all_execution_logs():
        items = Database.execution_log.find()
        return items

    @staticmethod # Delete Latest Execution Log
    def delete_execution_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.execution_log.delete_one(query)

    @staticmethod # Delete All Execution Logs of symbol
    def delete_execution_logs(symbol: str):
        query = {"Symbol": symbol}
        items = Database.execution_log.delete_many(query)

    @staticmethod # Delete ALL Execution Logs
    def delete_all_execution_logs():
        items = Database.execution_log.delete_many({})
    #endregion

    #region Commission Logs
    @staticmethod # Insert New Commission Log
    def insert_commission_log(execid: str, datetime: dt.datetime, commission: float, realizedpnl: float):
        execution = Database.read_execution_log_by_id(execid)
        if execution != None:
            symbol = execution["Symbol"]
            instruction = execution["Instruction"]
            ordertype = execution["OrderType"]
            
            data = {"Symbol": symbol, "DateTime": datetime, "Commission": commission, "RealizedPnL": realizedpnl, "OrderType": ordertype, "Instruction": instruction, "ExecId": execid}
            Database.commission_log.insert_one(data)
    
    @staticmethod # Read Latest Commission Log of symbol
    def read_commission_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.commission_log.find_one(query)
        return item
    
    @staticmethod # Read Latest Commission Log of id
    def read_commission_log_by_id(execid: str):
        query = {"ExecId": execid}
        item = Database.commission_log.find_one(query)
        return item

    @staticmethod # Read All Commission Logs of symbol
    def read_commission_logs(symbol: str):
        query = {"Symbol": symbol}
        items = Database.commission_log.find(query)
        return items

    @staticmethod # Read ALL Commission Logs
    def read_all_commission_logs():
        items = Database.commission_log.find()
        return items

    @staticmethod # Delete Latest Commission Log
    def delete_commission_log(symbol: str):
        query = {"Symbol": symbol}
        item = Database.commission_log.delete_one(query)

    @staticmethod # Delete All Commission Logs of symbol
    def delete_commission_logs(symbol: str):
        query = {"Symbol": symbol}
        items = Database.commission_log.delete_many(query)

    @staticmethod # Delete ALL Commission Logs
    def delete_all_commission_logs():
        items = Database.commission_log.delete_many({})
    #endregion

    #region Account Info Logs
    @staticmethod # Insert New Account Info
    def insert_account_info(accountid: str, datetime: dt.datetime, infotype: str, value: float):
        data = {"AccountId": accountid, "DateTime": datetime, "Type": infotype, "Value": value}
        insert = Database.account_info.insert_one(data)
    
    @staticmethod # Read Latest Account Info of Account ID
    def read_latest_account_info(accountid: str):
        query = {"AccountId": accountid}
        item = Database.account_info.find_one(query)
        return item

    @staticmethod # Read All Account info of Account ID
    def read_all_account_info(accountid: str):
        query = {"AccountId": accountid}
        items = Database.account_info.find(query)
        return items

    @staticmethod # Read All Account info of Account ID
    def read_all_accounts_info():
        items = Database.account_info.find()
        return items

    @staticmethod # Delete Latest Commission Log
    def delete_latest_account_info(accountid: str):
        query = {"AccountId": accountid}
        item = Database.account_info.delete_one(query)

    @staticmethod # Delete All Commission Logs of symbol
    def delete_account_info(accountid: str):
        query = {"AccountId": accountid}
        items = Database.account_info.delete_many(query)

    @staticmethod # Delete ALL Commission Logs
    def delete_all_account_info():
        items = Database.account_info.delete_many({})
    #endregion

    #region Error Logs
    @staticmethod # Insert New Error Log
    def insert_error_log(datetime: dt.datetime, error: str, filename: str, line: int):
        data = {"DateTime": datetime, "Error": error, "FileName": filename, "Line": line}
        insert = Database.error_log.insert_one(data)
    
    @staticmethod # Read Latest Error Log
    def read_latest_error_log():
        item = Database.error_log.find_one()
        return item

    @staticmethod # Read All Error Logs
    def read_all_error_logs():
        items = Database.error_log.find()
        return items

    @staticmethod # Delete Latest Error Log
    def delete_latest_error_log():
        item = Database.error_log.delete_one({})

    @staticmethod # Delete ALL Error Logs
    def delete_all_error_logs():
        items = Database.error_log.delete_many({})
    #endregion

    #region Daily Email Reports
    @staticmethod
    def mail_read_owned_shares():
        query = {"Shares": { "$gt" : 0 } }
        items = Database.symbols.find(query)
        return items
    
    @staticmethod
    def mail_read_open_orders():
        query = {"Filled": False, "Canceled": False}
        items = Database.order_log.find(query)
        return items
    
    @staticmethod
    def mail_read_account_info():
        results = {}
        for item in ['cashbalance','realizedpnl','netliquidationbycurrency','pasharesvalue','totalcashbalance']:
            query = {"Type": item}
            result = Database.account_info.find(query)
            results[item] = result["Value"]
        return results
    
    @staticmethod
    def mail_read_todays_executions():
        query = {"DateTime": { "$gt" : dt.datetime.now()-dt.timedelta(days=1) } }
        items = Database.execution_log.find(query)
        return items

    @staticmethod
    def mail_read_weeks_of_executions(weekcount):
        query = {"DateTime": { "$gt" : dt.datetime.now()-dt.timedelta(weeks=weekcount) } }
        items = Database.execution_log.find(query)
        return items

    
    #endregion