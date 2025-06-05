# Created by Yossy on 2025/06/04

from pathlib import Path
import json
import os

from utils import OBSItems


DEFAULT_TEMPLATE = Path('obs_templates') / 'yossy_tournaments_v01.json'
EXPORT_FILE = 'my_obs_config.json'
FILE_KEYS = ['file', 'local_file']

OBS_ITEMS = OBSItems()

def generate_obs_config(template=DEFAULT_TEMPLATE):
    "Generate OBS config file from a template"

    # Load OBS config template file 
    data = json.load(open(template, 'r', encoding='utf-8'))

    # Update file paths
    update_file_paths(data)

    # Export
    with open(EXPORT_FILE, 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, indent=4)
        
def update_file_paths(data):
    for file_key in FILE_KEYS:
        if issubclass(data.__class__, dict):
            for key in data.keys():
                if key == file_key and data[key].startswith('$'):
                    # Update path
                    item_key = data[key].lstrip('$')
                    abspath = os.path.abspath(OBS_ITEMS.key_to_item(item_key)['relative_path'])
                    data[key] = abspath
                    print("Updated path: {} > {}".format(item_key, abspath))

                # Recursive process
                update_file_paths(data[key])

        if issubclass(data.__class__, list):
            for item in data:
                # Recursive process
                update_file_paths(item)


def find_key(data, file_key):
    if issubclass(data.__class__, dict):
        for key in data.keys():
            find_key(data[key], file_key)
            if key == file_key and data[key] != "":
                print("Key found: {}\n {}: {}".format(data, file_key, data[file_key]))
    if issubclass(data.__class__, list):
        for item in data:
            find_key(item, file_key)

if __name__ == '__main__':
    generate_obs_config()

