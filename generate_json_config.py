import json
import os

def generate_json_config(start_index, end_index):
    with open('script_inputs/proxy.txt', 'r') as file:
        res_proxy = file.readline().strip()

    with open('script_inputs/datacenter_proxy.txt', 'r') as file:
        datacenter_proxies = [line.strip() for line in file.readlines()]

    with open('script_inputs/usernames.txt', 'r') as file:
        all_usernames = [line.strip() for line in file.readlines()]

    usernames = all_usernames[start_index:end_index]

    config = {
        "res-proxy": res_proxy,
        "datacenter-proxies": datacenter_proxies,
        "usernames": usernames
    }

    json_file_path = 'config.json'
    with open(json_file_path, 'w') as json_file:
        json.dump(config, json_file, indent=4)
    
    print(f"Configuration JSON written to {json_file_path}")
    return config

generate_json_config(0, 100000)