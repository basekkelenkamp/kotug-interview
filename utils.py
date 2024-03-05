import json
from math import radians, cos, sin, asin, sqrt


def read_json(file_path) -> dict:
    with open(file_path) as file:
        data = json.load(file)
    return data["data"]


def haversine(location1: dict, location2: dict) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    lon1, lat1 = location1["long"], location1["lat"]
    lon2, lat2 = location2["long"], location2["lat"]

    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r
