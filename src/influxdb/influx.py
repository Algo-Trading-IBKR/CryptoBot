import influxdb_client
from influxdb_client import Point, WritePrecision, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS # or ASYNCHRONOUS
from datetime import datetime
from time import sleep

class Influx:
    def __init__(self, config):
        self.org = str(config[0])
        self.token = str(config[1])
        self.url = str(config[2])

        # print(config)

        self.client = influxdb_client.InfluxDBClient.from_config_file("./src/influxdb/config.ini")

        self.write_api = self.client.write_api(write_options=WriteOptions(batch_size=500,
                                                flush_interval=10000,
                                                jitter_interval=2000,
                                                retry_interval=10000,
                                                max_retries=5,
                                                max_retry_delay=10000,
                                                exponential_base=2))
        self.query_api = self.client.query_api()


    def write(self, bucket, record):
        try:
            self.write_api.write(bucket = bucket, record=record)
        except Exception as e:
            self.bot.log.warning('INFLUX', f'Write Failed: {str(e)}.')
    
    def fetch(self, query):
        try:
            result = self.query_api.query(org=self.org, query=query)
            return result
        except Exception as e:
            self.bot.log.warning('INFLUX', f'Query Failed: {str(e)}.')
            return False

    def write_order(self, coin, order_id, side, order_type, amount, price, piramidding : bool = False):
        amount = float(amount)
        price = float(price)
        point = Point("order") \
                .tag("discord_id", coin.bot.user["discord_id"]) \
                .tag("order_id", order_id) \
                .tag("side", side) \
                .tag("order_type", order_type) \
                .tag("coin", coin.symbol) \
                .tag("currency", coin.currency) \
                .field("amount", amount) \
                .field("price", price) \
                .field("total", amount*price) \
                .field("piramidding", piramidding) \
                .time(datetime.utcnow(), WritePrecision.S)
        self.write(bucket="orders", record=point)
        
    def write_trade(self, coin, order_id, side, order_type, amount, price, fee, fee_currency, profit : float = 0.0, piramidding : bool = False):
        amount = float(amount)
        price = float(price)
        fee = float(fee)

        if side == "SELL":
            query = f'from(bucket: "trades")\
                    |> range(start: 0, stop: now())\
                    |> filter(fn:(r) => r["discord_id"] == "{coin.bot.user["discord_id"]}")\
                    |> filter(fn:(r) => r["coin"] == "{coin.symbol}")\
                    |> filter(fn:(r) => r["currency"] == "{coin.currency}")\
                    |> filter(fn:(r) => r["side"] == "BUY")\
                    |> limit(n: 2)\
                    |> sort(columns: ["_time"], desc: false)'
            # desc false very important
            result = self.fetch(query)
            for table in result:
                for row in table:    
                    if row.get_field() == "piramidding": 
                        buy_piramidding = row.get_value()

            buy_total = 0
            # always last item will decide (newest)
            if buy_piramidding:
                for table in result:
                    for row in table:
                        if row.get_field() == "total": buy_total += row.get_value()
            else:
                for table in result:
                    for row in table:
                        if row.get_field() == "total": buy_total = row.get_value() # last row will decide te value, so the latest buy in theory

            profit = (amount*price)-buy_total

        point = Point("trade") \
                .tag("discord_id", coin.bot.user["discord_id"]) \
                .tag("order_id", order_id) \
                .tag("side", side) \
                .tag("order_type", order_type) \
                .tag("coin", coin.symbol) \
                .tag("currency", coin.currency) \
                .field("amount", amount) \
                .field("price", price) \
                .field("total", amount*price) \
                .field("fee", fee) \
                .field("fee_currency", fee_currency) \
                .field("profit", profit) \
                .field("piramidding", piramidding) \
                .time(datetime.utcnow(), WritePrecision.S)
        self.write(bucket="trades", record=point)
