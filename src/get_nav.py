from concurrent.futures import ThreadPoolExecutor
from mftool import Mftool
import csv
import time

mf = Mftool()
keys = []
nav_field = ['date', 'nav']

with open('../Data/Fund_Index.csv', 'r', newline='') as l:
    reader = csv.DictReader(l)
    for k in reader:
        keys.append(k['scheme_code'])


def log_fund(key):
    time.sleep(0.5)
    raw = mf.get_scheme_historical_nav(key)
    with open(f"Data/Fund_Nav/{raw["fund_house"]}.csv", "w", newline='') as nav:
        writer = csv.DictWriter(nav, fieldnames=nav_field)
        writer.writeheader()
        for entry in raw['data']:
            writer.writerow({fields: entry[fields] for fields in nav_field})
        return key



def main():
    with open('../Data/Checkpoint.txt', 'r') as c:
        current = int(c.read())
    with ThreadPoolExecutor() as executor:
        r = executor.map(log_fund, keys[current:])
        for key, i in zip(keys, r):
            if i is None:
                print(f"Skipping {key}")
                continue
            current += 1
            print(f"Currently on {current}")
            with open('../Data/Checkpoint.txt', 'w') as ckpt:
                ckpt.write(str(current))

if __name__ == '__main__':
    main()