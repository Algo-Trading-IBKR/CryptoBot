import influxdb_client
from influxdb_client.client.write_api import ASYNCHRONOUS # or SYNCHRONOUS

class Influx:
    def __init__(self, config):
        self.bucket = config[0]
        self.org = config[1]
        self.token = config[2]
        self.url = config[3]

        self.client = influxdb_client.InfluxDBClient(
            url=self.url,
            token=self.token,
            org=self.org
        )
        
        self.write_api = self.client.write_api(write_options=ASYNCHRONOUS)
        self.query_api = self.client.query_api()

    def write(self, record):
        self.write_api.write(bucket=self.bucket, org=self.org, record=record)
    
    def fetch(self, query):
        self.query_api().query(org=self.org, query=query)








