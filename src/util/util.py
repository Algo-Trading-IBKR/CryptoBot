import json

def load_json(path):
    with open(path) as file:
        return json.load(file)
