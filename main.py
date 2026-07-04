
from mftool import Mftool
import csv

mf = Mftool()

keys = []

with open("Data/Directory.csv", "r", newline='') as d:
    reader = csv.DictReader(d, fieldnames=['Scheme Code', 'Scheme Name'])
    for code in reader:
        keys.append(code['Scheme Code'])



field_names = [
    "fund_house","scheme_type","scheme_category",
    "scheme_code","scheme_name","scheme_start_date",
    "52_week_high","52_week_low"]

nav_field = ['date', 'nav']

for key in keys[8800:]:
    raw = mf.get_scheme_historical_nav(key)
    if raw == None:
        continue
    with open("Data/Fund_Data.csv", "a", newline='') as fund:
        writer = csv.DictWriter(fund, fieldnames=field_names, extrasaction='ignore')
        writer.writerow({field: raw[field] for field in field_names})

    # with open(f"Data/{raw["fund_house"]}.csv", "w", newline='') as nav:
    #     writer = csv.DictWriter(nav, fieldnames=nav_field)
    #     writer.writeheader()
    #     for entry in raw['data']:
    #         writer.writerow({fields: entry[fields] for fields in nav_field})