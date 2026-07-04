from mftool import Mftool
import csv

mf = Mftool()

keys = []

with open("../Data/Directory.csv", "r", newline='') as d:
    reader = csv.DictReader(d, fieldnames=['Scheme Code', 'Scheme Name'])
    for code in reader:
        keys.append(code['Scheme Code'])

nav_field = ['date', 'nav']
item = 0

for key in keys:
    raw = mf.get_scheme_historical_nav(key)
    with open(f"Data/Fund_Nav/{raw["fund_house"]}.csv", "w", newline='') as nav:
        writer = csv.DictWriter(nav, fieldnames=nav_field)
        writer.writeheader()
        for entry in raw['data']:
            writer.writerow({fields: entry[fields] for fields in nav_field})

