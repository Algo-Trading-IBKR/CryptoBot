import requests
import json

class questdb:
    def __init__(self, url):
        self._url = url if url[-1] == "/" or url[-1] == "\\" else url+"/"

    def get(self, query):
        result = requests.get(self._url + "exec?query" + query)
        return result
    
    def post(self, query):
        result = requests.post(self._url + "exec", params={'query': query})
        json_response = json.loads(result.text)
        return json_response