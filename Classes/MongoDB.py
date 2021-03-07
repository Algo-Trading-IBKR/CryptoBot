import pymongo
import datetime as dt
from DatabaseRepository_TradingBot import Database

# client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
# db = client["CryptoBot"]
# symbols = db["Symbols"]


def test_symbols():
    print('Symbol Test')    
    Database.insert_symbol('AMD', dt.datetime.now(),0.0, 0.0, 0.0, 0.0)
    Database.update_symbol('AMD', dt.datetime.now(),2.4, 3.8, 4.1, 5.6) 
    symbolitem = Database.read_symbol('AMD')
    # print(symbolitem)
    symbolitems = Database.read_all_symbols()
    for item in symbolitems:
        print(item)
    # Database.delete_symbol('AMD')
    # Database.delete_all_symbols()

test_symbols()


# client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
# client = pymongo.MongoClient("mongodb://localhost:27017")
# db = client.pymongo_test
