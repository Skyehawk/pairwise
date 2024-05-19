import json

def update_entry_count(FILE, entry_date, entry_count):
    with open(FILE, 'r') as json_file:
        data = json.load(json_file)

    if entry_date not in data['total_entries']:
        data['total_entries'][entry_date] = 0

    data['total_entries'][entry_date] += entry_count

    with open(FILE, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def update_entry_counts(FILE, date_count_dict):
    for date, count in date_count_dict.items():
        update_entry_count(FILE, date, count)

    print("Entry counts updated successfully.")

def get_entry_counts(FILE):
    try:
        with open(FILE, "r") as file:
            entry_counts = json.load(file)
    except FileNotFoundError:
        entry_counts = {}

    return entry_counts