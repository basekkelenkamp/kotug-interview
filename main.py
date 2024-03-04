from pprint import pprint
from dateutil.parser import parse
from utils import read_json, haversine


def clean_and_transform(data: dict):
    mmsi_list = []
    count_duplicates = 0
    unique_vessel_types = []
    unique_names = []
    unique_status = []

    for item in data:
        for key in item.keys():
            if key not in ["vessel", "navigation", "device"]:
                raise Exception(f"Unknown key: {key}")

        if not item["vessel"]["name"] in unique_names:
            unique_names.append(item["vessel"]["name"])

        if not item["vessel"]["type"] in unique_vessel_types:
            unique_vessel_types.append(item["vessel"]["type"])

        if not item["navigation"]["status"] in unique_status:
            unique_status.append(item["navigation"]["status"])
        if item["device"]["mmsi"] in mmsi_list:
            count_duplicates += 1
        else:
            mmsi_list.append(item["device"]["mmsi"])

        # Transform time
        item["navigation"]["time"] = parse(item["navigation"]["time"])

    print("\n-- Data Summary --")
    print(f"{'Unique vessel names:':<25} {', '.join(unique_names)}")
    print(f"{'Unique vessel types:':<25} {', '.join(unique_vessel_types)}")
    print(f"{'Unique status:':<25} {', '.join(unique_status)}")
    print(f"{'Total MMSIs:':<25} {len(mmsi_list)}")
    print(f"{'Duplicate MMSIs:':<25} {count_duplicates}")
    print("-- end --\n")
    return data


def extract_vessel_data(data: dict):
    vessel_data = {}
    for item in data:
        mmsi = str(item["device"]["mmsi"])
        if not mmsi in vessel_data:
            # Static values
            vessel_data[mmsi] = {
                "name": item["vessel"]["name"],
                "type": item["vessel"]["type"],
                "sub_type": item["vessel"]["subtype"],
                "vessel_callsign": item["vessel"]["callsign"],
                "vessel_imo": item["vessel"]["imo"],
                "dynamic_values": [],
            }

        # Dynamic values
        vessel_data[mmsi]["dynamic_values"].append(
            {
                "status": item["navigation"]["status"],
                "time": item["navigation"]["time"],
                "speed": item["navigation"]["speed"],
                "location": item["navigation"]["location"],
                "course": item["navigation"]["course"],
            }
        )

    return vessel_data

def sort_by_time(dynamic_values: dict):
    return sorted(dynamic_values, key=lambda x: x["time"])


if __name__ == "__main__":
    data = read_json("data/port_arthur.json")
    data = clean_and_transform(data)

    vessels = extract_vessel_data(data)

    for mmsi, vessel in vessels.items():
        vessel["dynamic_values"] = sort_by_time(vessel["dynamic_values"])

