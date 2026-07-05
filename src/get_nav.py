import csv
import time
from pathlib import Path
import re
from mftool import Mftool

mf = Mftool()

# --- Configuration ---
INDEX_FILE = Path('../Data/Fund_Index.csv')
MASTER_CSV = Path('../Data/all_nav.csv')
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
# Helper to safely clean fund house names for CSV (they are just strings, but just in case)
def safe_name(name):
    # Replace characters that might cause issues (though not strictly necessary for CSV values)
    return re.sub(r'[\n\r]', ' ', str(name))

# ----------------------------------------------------------------------
# Open the master CSV once (append mode) and write header if it's new
file_exists = MASTER_CSV.exists()
with MASTER_CSV.open('a', newline='', encoding='utf-8') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=OUTPUT_FIELDS)
    if not file_exists:
        writer.writeheader()

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
        fund_house = safe_name(raw['fund_house'])
        nav_data = raw['data']   # should be a list of dicts with 'date' and 'nav'

        if not isinstance(nav_data, list):
            print(f"  'data' field is not a list — skipping.")
            continue

        # --- Write all daily NAV rows for this fund ---
        rows_written = 0
        try:
            for entry in nav_data:
                # Some entries might be missing 'date' or 'nav' — skip those
                if 'date' not in entry or 'nav' not in entry:
                    continue
                writer.writerow({
                    'fund_house': fund_house,
                    'scheme_code': key,
                    'date': entry['date'],
                    'nav': entry['nav']
                })
                rows_written += 1
            # Flush to disk so we don't lose data if interrupted
            outfile.flush()
        except Exception as e:
            print(f"  Write error: {e}")
            continue

        print(f"  → Wrote {rows_written} rows.")

        # --- Update checkpoint after successful write ---
        CHECKPOINT_FILE.write_text(key)

print("Done! Master CSV is ready for Pandas.")