from tqdm.contrib.concurrent import thread_map
from dotenv import load_dotenv
from datetime import datetime
from mftool import Mftool
import psycopg2.extras
import psycopg2.pool
import psycopg2
import random
import json
import time
import os

mf = Mftool()

# --- Configuration ---
MAX_RETRIES = 5
BASE_DELAY = 1.0


# -----------------Data Base Related ---------------------------
# --- Initialize the DataBase ---
load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

# --- Test Connection ---
con = None
try:

    # Start The Test
    print(
        f"Trying to connect to DataBase: {DB_CONFIG['dbname']} as user {DB_CONFIG['user']}"
    )
    con = psycopg2.connect(**DB_CONFIG)

    # Display info
    cursor = con.cursor()
    cursor.execute("SELECT version()")
    db_ver = cursor.fetchone()

    # print info if successful
    print(f"Connection Successful, PostgreSQL version {db_ver[0]}")

    # --- Table to track Progress ---
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS checkpoint_nav
           (
               scheme_code      INT PRIMARY KEY REFERENCES fund_index(scheme_code) ON DELETE CASCADE,
               last_synced      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               status           VARCHAR(20) DEFAULT 'COMPLETED'
           )
    """)

    # --- Connecting and Creating a sqlite database ---
    cursor.execute("""
           CREATE TABLE IF NOT EXISTS historical_nav
           (
                id                  SERIAL PRIMARY KEY,
                scheme_code         INT REFERENCES fund_index(scheme_code) ON DELETE CASCADE,
                nav_date            DATE,
                nav                 REAL,
                UNIQUE (scheme_code, nav_date)
            );
    """)
    con.commit()

except psycopg2.OperationalError as e:
    print("Connection failed. Check your credentials or server status.")
    print(e)
    exit(1)

# --- Load the Keys ---
keys = sorted(list(mf.get_scheme_codes()))

# --- Load already completed keys ---
cursor.execute("SELECT scheme_code FROM checkpoint_nav")
completed = {str(row[0]) for row in cursor.fetchall()}
remaining_keys = [k for k in keys if k not in completed]
print(f"{len(remaining_keys)}: Scheme Codes Left to be Processed")

cursor.close()
con.close()

db_pool = psycopg2.pool.ThreadedConnectionPool(minconn=5, maxconn=20, **DB_CONFIG)


# ----------------------------------------------------------------------
# Function to process each fund
def process_fund(key):

    # open connection per worker
    conn = db_pool.getconn()
    cur = conn.cursor()

    # --- Fetch data (with retry/error handling) ---
    try:

        raw = None
        attempt = 0
        # --- The Exponential Backoff Loop ---
        while attempt < MAX_RETRIES:
            try:
                # Baseline Jitter
                time.sleep(random.uniform(0.1, 0.5))

                # API Call
                raw = mf.get_scheme_historical_nav(key)

                # If it succeeds without throwing a network error, break the retry loop!
                break

            except Exception as e:
                attempt += 1
                if attempt >= MAX_RETRIES:
                    # Attempt according to max retries
                    return key, False, 0, f"Max retries reached. Last error: {e}"

                # Calculate Exponential Backoff + Jitter
                sleep_time = (BASE_DELAY * (2 ** (attempt - 1))) + random.uniform(
                    0, 1.0
                )
                time.sleep(sleep_time)

        # --- validating ---
        if raw is None:
            return key, False, 0, "API Returned None"

        if not isinstance(raw, dict) or "fund_house" not in raw or "data" not in raw:
            return key, False, 0, "Data Scheme is Incorrect"

        # --- Extract common info ---
        nav_data = raw.get("data")  # should be a list of dicts with 'date' and 'nav'

        if not isinstance(nav_data, list):
            return key, False, 0, "Nav Data doesn't match the requirements"

        # --- Enter all the rows for a fund in the database ---
        rows_inserted = 0
        rows = []
        for entry in nav_data:
            if "date" not in entry or "nav" not in entry:
                continue
            try:
                clean_date = datetime.strptime(entry["date"], "%d-%m-%Y").strftime(
                    "%Y-%m-%d"
                )

                rows.append((key, clean_date, float(entry["nav"])))
                rows_inserted += 1
            except (ValueError, TypeError):
                continue

        if not rows:
            return key, False, 0, "Rows were Empty"
        insert_query = """
                       INSERT INTO historical_nav (scheme_code, nav_date, nav) 
                       VALUES %s
                       ON CONFLICT (scheme_code, nav_date) DO NOTHING 
                       """
        psycopg2.extras.execute_values(cur, insert_query, rows)

        checkpoint_query = """
                           INSERT INTO checkpoint_nav (scheme_code, status)
                           VALUES (%s, 'COMPLETED') 
                           ON CONFLICT (scheme_code) DO NOTHING 
                           """
        cur.execute(checkpoint_query, (key,))
        conn.commit()

        return key, True, rows_inserted, "Success"

    except Exception as e:
        conn.rollback()
        return key, False, 0, str(e)  # Pass the error message back

    finally:
        cur.close()
        db_pool.putconn(conn)


# ----------------------------------------------------------------------
failed = 0
try:

    results = thread_map(
        process_fund,
        remaining_keys,
        max_workers=20,
        desc="Ingesting Funds",
        unit="Funds",
    )
    failed = 0
    # Log the progress in a .jsonl file
    with open("../Data/nav_logs.jsonl", "w", newline="\n") as log:

        for result_key, success, rows_count, message in results:

            log_record = {
                "timestamp": datetime.now().isoformat(),
                "scheme_code": result_key,
                "status": "SUCCESS" if success else "FAILED",
                "rows_inserted": rows_count,
                "message": message,
            }

            log.write(json.dumps(log_record) + "\n")

            if not success:
                failed += 1


except Exception as e:
    print(f"Unknown thread crash : {e}")


finally:
    if "db_pool" in globals():
        db_pool.closeall()
        print("\nAll database pool connections closed cleanly.")

    print(f"Done! {failed} funds failed. Database is ready!")
