from mftool import Mftool
import csv

mf = Mftool()

keys = []
with open("Data/Directory.csv", "r", newline='') as d:
    reader = csv.DictReader(d, fieldnames=['Scheme Code', 'Scheme Name'])
    for code in reader:
        keys.append(code['Scheme Code'])


raw = mf.get_scheme_historical_nav("119551")

print(gen_keys())
print(type(raw))