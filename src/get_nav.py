from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from mftool import Mftool
from pathlib import Path
import sqlite3
import time
import csv



mf = Mftool()

# --- Configuration ---
INDEX_FILE = Path('../Data/Fund_Index.csv')
DB_PATH = Path('../Data/Nav_Data.db')
SLEEP_SECONDS = 0.5   # adjust as needed to avoid rate limiting

# Fields we write to the master CSV
OUTPUT_FIELDS = ['fund_house', 'scheme_code', 'date', 'nav']

# ----------------------------------------------------------------------
# Load all scheme codes from the index
with INDEX_FILE.open('r', newline='') as f:
    reader = csv.DictReader(f)
    keys = [row['scheme_code'] for row in reader]

print(f"Loaded {len(keys)} scheme codes.")



# -----------------Data Base Related ---------------------------
# --- Initialize the DataBase ---
con = sqlite3.connect(DB_PATH)
cursor = con.cursor()

# --- Table to track Progress ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS checkpoint(
        scheme_code     TEXT PRIMARY KEY,
        completed_at    TEXT
    )
''')

# --- Connecting and Creating a sqlite database ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS nav_data (
        fund_house    TEXT,
        scheme_code   TEXT,
        date          TEXT,
        nav           REAL
    )
''')

# --- Making tables safe for concurrency ---
cursor.execute('PRAGMA journal_mode=WAL')
con.commit()

# --- Load already completed keys ---
cursor.execute('SELECT scheme_code FROM checkpoint')
completed = {row[0] for row in cursor.fetchall()}
remaining_keys = [k for k in keys if k not in completed]


# ----------------------------------------------------------------------
# Function to process each fund
def process_fund(key):

    # Be polite to the API
    time.sleep(SLEEP_SECONDS)

    # open connection per worker
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print(f"Currently Processing: {key}  ")

    # --- Fetch data (with retry/error handling) ---
    try:
        raw = mf.get_scheme_historical_nav(key)
        # --- validating ---
        if raw is None:
            print(f"  Returned None for code: {key} — skipping.")
            return key, False

        if not isinstance(raw, dict) or 'fund_house' not in raw or 'data' not in raw:
            print(f"  Unexpected structure: {raw if isinstance(raw, dict) else type(raw)}")
            return key, False

        # --- Extract common info ---

        fund_house = raw['fund_house']
        nav_data = raw['data']  # should be a list of dicts with 'date' and 'nav'

        if not isinstance(nav_data, list):
            print(f"  'data' field is not a list for code {key} — skipping.")
            return key, False

        # --- Enter all the rows for a fund in the database ---
        rows_inserted = 0
        try:
            rows = []
            for entry in nav_data:
                # Some entries might be missing 'date' or 'nav' — skip those
                if 'date' not in entry or 'nav' not in entry:
                    continue
                rows.append((fund_house, key, entry['date'], entry['nav']))
                rows_inserted += 1
            cur.executemany('INSERT INTO nav_data VALUES (?, ?, ?, ?)', rows)

            # --- Update checkpoint after successful insertion ---
            cur.execute('INSERT OR IGNORE INTO checkpoint VALUES (? ,?)',
                        (key, datetime.now().isoformat()))

            conn.commit()
        except Exception as e:
            print(f"Insertion error: {e}")
        print(f"    → Wrote {rows_inserted} rows for code {key}. ")
        return key, True

    except Exception as e:
        print(f"  API error: {e}")
        return key, False
    finally:
        conn.close()
# ----------------------------------------------------------------------

# Process keys with multithreading and logging the status on console
try:
    with ThreadPoolExecutor(max_workers=5) as executor:
        result = executor.map(process_fund, remaining_keys)
        failed = 0
        for key, success in result:
            if not success:
                failed += 1

    # --- Cleanup ---
    if not remaining_keys:
        # Everything was already done before this run
        cursor.execute('DROP TABLE IF EXISTS checkpoint')
        con.commit()
        print("✓ All funds were already processed. Checkpoint deleted.")
    elif failed == 0:
        # This run completed everything
        cursor.execute('DROP TABLE IF EXISTS checkpoint')
        con.commit()
        print("✓ All funds processed successfully. Checkpoint deleted.")
    else:
        print(f"⚠️  {failed} funds failed. Checkpoint kept for resumption.")
finally:
    con.close()
    print("Done! Database is ready for Pandas.")