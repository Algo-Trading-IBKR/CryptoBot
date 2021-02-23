import pymongo
import datetime as dt


# client = pymongo.MongoClient("mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false")
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client.pymongo_test
