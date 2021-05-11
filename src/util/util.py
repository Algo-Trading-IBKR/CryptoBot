import json
import math

class util:
    @staticmethod
    def get_amount(number : float, decimals : int = 2, floor : bool = True) -> float:
        factor = 10 ** decimals

        return math.floor(number * factor) / factor if floor else math.ceil(number * factor) / factor

    @staticmethod
    def get_asset_and_quote(account : dict) -> tuple:
        return float(account["assets"][0]["baseAsset"]["free"]), float(account["assets"][0]["baseAsset"]["borrowed"]), float(account["assets"][0]["quoteAsset"]["free"]), float(account["assets"][0]["quoteAsset"]["borrowed"])

    @staticmethod
    def load_json(path : str) -> dict:
        with open(path) as file:
            return json.load(file)
