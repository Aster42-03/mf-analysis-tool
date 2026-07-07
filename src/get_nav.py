from concurrent.futures.thread import ThreadPoolExecutor
from dotenv import load_dotenv
from datetime import datetime
from mftool import Mftool
from pathlib import Path
import psycopg2
import time
import csv
import os

mf = Mftool()

# --- Configuration ---
load_dotenv()
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
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# --- Test Connection ---
con = None
try:

    # Start The Test
    print(f"Trying to connect to DataBase: {DB_CONFIG['dbname']} as user {DB_CONFIG['user']}")
    con = psycopg2.connect(**DB_CONFIG)

    # Display info
    cursor = con.cursor()
    cursor.execute('SELECT version()')
    db_ver = cursor.fetchone()

    # Print info if successful
    print(f"Connection Successful, PostgreSQL version {db_ver[0]}")

    # --- Table to track Progress ---
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS checkpoint
                   (
                       scheme_code
                       TEXT
                       PRIMARY
                       KEY,
                       completed_at
                       TEXT
                   )
                   ''')

    # --- Connecting and Creating a sqlite database ---
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS nav_data
                   (
                       fund_house
                       TEXT,
                       scheme_code
                       TEXT,
                       date
                       TEXT,
                       nav
                       REAL
                   )
                   ''')
    con.commit()

except psycopg2.OperationalError as e:
    print("Connection failed. Check your credentials or server status.")
    print(e)
    exit(1)

# --- Load already completed keys ---
cursor.execute('SELECT scheme_code FROM checkpoint')
completed = {row[0] for row in cursor.fetchall()}
remaining_keys = [k for k in keys if k not in completed]
print(f"{len(remaining_keys)}: Scheme Codes Left to be Processed")


# ----------------------------------------------------------------------
# Function to process each fund
def process_fund(key):

    # Be polite to the API
    time.sleep(SLEEP_SECONDS)

    # open connection per worker
    conn = psycopg2.connect(**DB_CONFIG)
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
                rows.append((fund_house, key, entry['date'], float(entry['nav'])))
                rows_inserted += 1
            insert_query = 'INSERT INTO nav_data (fund_house, scheme_code, date, nav) VALUES (%s, %s, %s, %s)'
            cur.executemany(insert_query, rows)

            # --- Update checkpoint after successful insertion ---
            checkpoint_query = '''
                               INSERT INTO checkpoint (scheme_code, completed_at)
                               VALUES (%s, %s) ON CONFLICT (scheme_code) DO NOTHING 
                               '''
            cur.execute(checkpoint_query, (key, datetime.now().isoformat()))

            conn.commit()
        except Exception as e:
            print(f"Insertion error: {e}")
            conn.rollback()
            return key, False

        print(f"    → Wrote {rows_inserted} rows for code {key}. ")
        return key, True

    except Exception as e:
        print(f"  API error: {e}")
        return key, False
    finally:
        cur.close()
        conn.close()
# ----------------------------------------------------------------------

# Process keys with multithreading and logging the status on console
try:
    with ThreadPoolExecutor(max_workers=5) as executor:
        result = executor.map(process_fund, remaining_keys)
        failed = 0
        for k, success in result:
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
        print(f"  {failed} funds failed. Checkpoint kept for resumption.")
finally:
    cursor.close()
    con.close()
    print("Done! Database is ready for Pandas.")