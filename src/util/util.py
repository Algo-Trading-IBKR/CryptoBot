import json
import math

class util:
    @staticmethod
    def get_amount(number : float, decimals : int = 2, floor : bool = True) -> float:
        factor = 10 ** decimals

        return math.floor(number * factor) / factor if floor else math.ceil(number * factor) / factor

    @staticmethod
    def load_json(path):
        with open(path) as file:
            return json.load(file)
