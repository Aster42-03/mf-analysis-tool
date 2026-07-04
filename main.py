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
    "52_week_high","52_week_low"
]

nav_field = ['date', 'nav']

with open("Data/Fund_Data.csv", "a", newline='') as fund:
    writer = csv.DictWriter(fund, fieldnames=field_names, extrasaction='ignore')
    for key in keys[11190:]:
        raw = mf.get_scheme_historical_nav(key)
        if raw == None:
            continue

        writer.writerow({field: raw[field] for field in field_names})

