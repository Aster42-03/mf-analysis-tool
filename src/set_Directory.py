from mftool import Mftool
import csv

mf = Mftool()

r = mf.get_scheme_codes()

fields = ['scheme_name', 'scheme_code']

with open('../Data/Directories.csv', "w", newline='', encoding='utf-8') as d:
    writer = csv.writer(d)
    for key, value in r.items():
        writer.writerow([key, value])