from dateutil.parser import parse
from utils import read_json, haversine
from time import sleep
from pprint import pprint
from datetime import datetime
from copy import deepcopy

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

    # for v in vessel_data.values():
    #     print(f"{v['name']}")
    #     print(f"Dynamic values: {len(v['dynamic_values'])}")
    # breakpoint()
    return vessel_data


def print_dynamic_vessel_data(vessel_dynamic_values: dict, sleep_time: float = 0.1):
    for dyn_item in vessel_dynamic_values:
        long, lat = dyn_item["location"]["long"], dyn_item["location"]["lat"]
        time_string = dyn_item["time"].strftime("%A, %B %d, %Y - %I:%M %p")
        speed = dyn_item["speed"]
        print(f"{time_string :<40} long/lat: {long:<10} {lat:<15} speed: {speed:<5}")
        sleep(sleep_time)


def sort_by_time(dynamic_values: dict):
    return sorted(dynamic_values, key=lambda x: x["time"])


def format_time(time):
    return time.strftime("%A, %B %d, %Y - %I:%M %p")


def split_tugs_and_non_tugs(vessels: dict):
    tugs = {}
    non_tugs = {}
    for vessel in vessels.values():
        if vessel["type"] == "tug":
            tugs[vessel["name"]] = vessel
        else:
            non_tugs[vessel["name"]] = vessel

    print("\n-- Tugs --")
    print("\n".join(tugs.keys()))
    print("\n-- Non-Tugs --")
    print("\n".join(non_tugs.keys()) + "\n")
    return tugs, non_tugs


def sync_time_for_vessels(v1: dict, v2: dict):
    v1_start_time = v1["dynamic_values"][0]["time"]
    v2_start_time = v2["dynamic_values"][0]["time"]

    v1_end_time = v1["dynamic_values"][-1]["time"]
    v2_end_time = v2["dynamic_values"][-1]["time"]

    while not compare_two_times(v1_start_time, v2_start_time):
        if v1_start_time < v2_start_time:
            del v1["dynamic_values"][0]
            v1_start_time = v1["dynamic_values"][0]["time"]
        else:
            del v2["dynamic_values"][0]
            v2_start_time = v2["dynamic_values"][0]["time"]

    while not compare_two_times(v1_end_time, v2_end_time):
        if v1_end_time > v2_end_time:
            del v1["dynamic_values"][-1]
            v1_end_time = v1["dynamic_values"][-1]["time"]
        else:
            del v2["dynamic_values"][-1]
            v2_end_time = v2["dynamic_values"][-1]["time"]

    return v1, v2


def compare_two_times(time1: datetime, time2: datetime, is_within_minutes: int = 2):
    return abs((time1 - time2).total_seconds()) < is_within_minutes * 60


def find_middle_index(lst):
    return len(lst) // 2


if __name__ == "__main__":
    data = read_json("data/port_arthur.json")
    data = clean_and_transform(data)

    vessels = extract_vessel_data(data)

    for mmsi, vessel in vessels.items():
        vessel["dynamic_values"] = sort_by_time(vessel["dynamic_values"])

        # print("\nVESSEL:", vessel["name"])
        # print_dynamic_vessel_data(vessel["dynamic_values"], sleep_time=0.005)

    tugs, non_tugs = split_tugs_and_non_tugs(vessels)
    input("Press enter to calculate distances...")
    distances = []
    for name, tug in tugs.items():
        for name, non_tug in non_tugs.items():
            # Create deep copies of tug and non_tug to avoid modifying the original data
            tug_copy = deepcopy(tug)
            non_tug_copy = deepcopy(non_tug)

            synced_tug, synced_non_tug = sync_time_for_vessels(tug_copy, non_tug_copy)

            tug_start_location = synced_tug["dynamic_values"][0]["location"]
            tug_end_location = synced_tug["dynamic_values"][-1]["location"]

            non_tug_start_location = synced_non_tug["dynamic_values"][0]["location"]
            non_tug_end_location = synced_non_tug["dynamic_values"][-1]["location"]

            tug_start_time = format_time(synced_tug["dynamic_values"][0]["time"])
            tug_end_time = format_time(synced_tug["dynamic_values"][-1]["time"])

            non_tug_start_time = format_time(
                synced_non_tug["dynamic_values"][0]["time"]
            )
            non_tug_end_time = format_time(synced_non_tug["dynamic_values"][-1]["time"])

            start_distance = haversine(tug_start_location, non_tug_start_location)
            end_distance = haversine(tug_end_location, non_tug_end_location)

            distances.append(
                {
                    "names": f"{tug['name']} <=> {non_tug['name']}",
                    "distance": f"start: {round(start_distance, 3)} km, end: {round(end_distance, 3)} km",
                    "start_times": f"tug: {tug_start_time} non-tug: {non_tug_start_time}",
                    "end_times": f"tug: {tug_end_time} non-tug: {non_tug_end_time}",
                    "len_timestamps": f"tug: {len(tug['dynamic_values'])} non-tug: {len(non_tug['dynamic_values'])}",
                }
            )

    for item in distances:
        print(f"-- {item['names']} --")
        print(f"Distance: {item['distance']}")
        print(f"Start times: {item['start_times']}")
        print(f"End times: {item['end_times']}")
        print(f"Timestamps: {item['len_timestamps']}\n")
    breakpoint()

    # TODO:
    # go through each tug/vessel and compare distance of all timestamps
