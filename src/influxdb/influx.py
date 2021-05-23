import influxdb_client
from influxdb_client import Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS # or ASYNCHRONOUS
from datetime import datetime

class Influx:
    def __init__(self, config):
        self.bucket = str(config[0])
        self.org = str(config[1])
        self.token = str(config[2])
        self.url = str(config[3])

        # print(config)

        self.client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org,
            debug=False
        )

        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()


        # point = Point("name") \
        #         .tag("discord_id", 1) \
        #         .tag("order_id", 2) \
        #         .tag("side", "SELL") \
        #         .tag("order_type", "limit") \
        #         .tag("coin", "DOGE") \
        #         .tag("currency", "USDT") \
        #         .field("amount", 5) \
        #         .field("price", 5) \
        #         .field("total", 10) \
        #         .field("piramidding", False) \
        #         .time(datetime.utcnow(), WritePrecision.S)
        # self.write_api.write(bucket = self.bucket, record=point)

        # query = f'from(bucket:"orders") |> range(start: -20m)'
        # result = self.fetch(query)
        # print(result)

    def write(self, record):
        self.write_api.write(bucket = self.bucket, record=record)
    
    def fetch(self, query):
        result = self.query_api.query(org=self.org, query=query)
        return result

    def write_order(self, coin, order_id, side, order_type, amount, price, total, piramidding : bool = False):
        point = Point("measurement name") \
                .tag("discord_id", coin.bot.user["discord_id"]) \
                .tag("order_id", order_id) \
                .tag("side", side) \
                .tag("order_type", order_type) \
                .tag("coin", coin.symbol) \
                .tag("currency", coin.currency) \
                .field("amount", amount) \
                .field("price", price) \
                .field("total", total) \
                .field("piramidding", piramidding) \
                .time(datetime.utcnow(), WritePrecision.S)
        self.write(point)
        
    def write_trade(self, coin, order_id, side, order_type, amount, price, total, fee, fee_currency, profit, piramidding : bool = False):
        # if side == "SELL":
        #     query = f"""from(bucket: self.bucket)
        #             |> filter(fn: (r) =>
        #                 r.discord_id == {coin.bot.user['discord_id']}
        #                 r.coin == {coin.symbol}
        #                 r.currency == {coin.currency}
        #             |> sort(columns: ['time'])
        #             |> last()
        #             |> limit(n: 1)
        #             )"""
        #     result = self.fetch(query)
        #     console.log(result)

        point = Point("measurement name") \
                .tag("discord_id", coin.bot.user["discord_id"]) \
                .tag("order_id", order_id) \
                .tag("side", side) \
                .tag("order_type", order_type) \
                .tag("coin", coin.symbol) \
                .tag("currency", coin.currency) \
                .field("amount", amount) \
                .field("price", price) \
                .field("total", total) \
                .field("fee", fee) \
                .field("fee_currency", fee_currency) \
                .field("profit", profit) \
                .field("piramidding", piramidding) \
                .time(datetime.utcnow(), WritePrecision.S)
        self.write(point)



# config = ['orders', 'crypto', 'm0DQvW6wvIdy0l2YN3dceFKR4LInurm4-yhoR5r0Uq95F-btt21K0GmFeZORbujdSwJ0iqosr5dHlhr-ghc9tA==', 'http://localhost:8086']
# influx = Influx(config)




