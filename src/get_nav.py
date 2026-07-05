import sqlite3
import time
import csv
from pathlib import Path
from mftool import Mftool


mf = Mftool()

# --- Configuration ---
INDEX_FILE = Path('../Data/Fund_Index.csv')
CHECKPOINT_FILE = Path('../Data/checkpoint.txt')
SLEEP_SECONDS = 0.5   # adjust as needed to avoid rate limiting

# Fields we write to the master CSV
OUTPUT_FIELDS = ['fund_house', 'scheme_code', 'date', 'nav']

# ----------------------------------------------------------------------
# Load all scheme codes from the index
with INDEX_FILE.open('r', newline='') as f:
    reader = csv.DictReader(f)
    keys = [row['scheme_code'] for row in reader]

print(f"Loaded {len(keys)} scheme codes.")

# ----------------------------------------------------------------------
# Determine where to resume
start_code = None
if CHECKPOINT_FILE.exists():
    start_code = CHECKPOINT_FILE.read_text().strip()
    if start_code and start_code in keys:
        start_idx = keys.index(start_code) + 1  # resume *after* the checkpoint key
    else:
        start_idx = 0
else:
    start_idx = 0

if start_idx > 0:
    print(f"Resuming from scheme code {keys[start_idx]} (index {start_idx})")
else:
    print("Starting from the beginning.")

# ----------------------------------------------------------------------

# Connecting and Creating a sqlite database
con = sqlite3.connect('../Data/Nav_Data.db')
cursor = con.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS nav_data (
        fund_house    TEXT,
        scheme_code   TEXT,
        date          TEXT,
        nav           REAL
    )
''')
# Process keys sequentially

for idx in range(start_idx, len(keys)):
    key = keys[idx]
    print(f"[{idx+1}/{len(keys)}] Processing {key}...")

    # Be polite to the API
    time.sleep(SLEEP_SECONDS)

    # --- Fetch data (with retry/error handling) ---
    try:
        raw = mf.get_scheme_historical_nav(key)
    except Exception as e:
        print(f"  API error: {e}")
        continue

    if raw is None:
        print(f"  Returned None — skipping.")
        continue

    if not isinstance(raw, dict) or 'fund_house' not in raw or 'data' not in raw:
        print(f"  Unexpected structure: {raw if isinstance(raw, dict) else type(raw)}")
        continue

    # --- Extract common info ---
    fund_house = raw['fund_house']
    nav_data = raw['data']   # should be a list of dicts with 'date' and 'nav'

    if not isinstance(nav_data, list):
        print(f"  'data' field is not a list — skipping.")
        continue

    # --- Enter all the rows for a fund in the database ---
    rows_written = 0
    try:
        rows = []
        for entry in nav_data:
            # Some entries might be missing 'date' or 'nav' — skip those
            if 'date' not in entry or 'nav' not in entry:
                continue
            rows.append((fund_house, key, entry['date'], entry['nav']))
            rows_written += 1
        cursor.executemany('INSERT INTO nav_data VALUES (?, ?, ?, ?)', rows)
        con.commit()
    except Exception as e:
        print(f"  Insertion error: {e}")
        continue

    print(f"  → Wrote {rows_written} rows.")

    # --- Update checkpoint after successful write ---
    CHECKPOINT_FILE.write_text(key)
con.close()
print("Done! Database is ready for Pandas.")