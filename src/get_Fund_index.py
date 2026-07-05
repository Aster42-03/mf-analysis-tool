from concurrent.futures import ThreadPoolExecutor
from mftool import Mftool
import csv
import os



mf = Mftool()

keys = []

with open('../Data/Directories.csv', 'r', newline='') as k:
    reader = csv.DictReader(k)
    for key in reader:
        keys.append(key['Scheme Code'])


field_names = [
    "fund_house","scheme_type","scheme_category",
    "scheme_code","scheme_name","scheme_start_date",
]


with open('../Data/Checkpoint.txt') as ct:
    current = int(ct.read())


with ThreadPoolExecutor(max_workers=5) as executor:
    raw_result = executor.map(mf.get_scheme_details, keys[current:])

    with open("../Data/Fund_Index.csv", "a", newline='') as fund:

        writer = csv.DictWriter(fund, fieldnames=field_names, extrasaction='ignore')
        file_exists = os.path.isfile("../Data/Fund_Index.csv") and os.path.getsize("../Data/Fund_Index.csv") > 0
        if not file_exists:
            writer.writeheader()
        for key, raw in zip(keys, raw_result):
            if raw is None:
                print(f"Skipping {key}")
                continue
            writer.writerow({field: raw[field] for field in field_names})
            current += 1
            print (f"Currently on {current}")
            with open('../Data/Checkpoint.txt', 'w') as ckpt:
                ckpt.write(str(current))
