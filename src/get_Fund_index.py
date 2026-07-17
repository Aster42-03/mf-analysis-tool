import json
import os
import random
import re
import time
from datetime import datetime

from dotenv import load_dotenv
from tqdm.contrib.concurrent import thread_map
import psycopg2
import psycopg2.pool
from mftool import Mftool

# --- Initialization ---
mf = Mftool()
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

keys = sorted(list(mf.get_scheme_codes().keys()))

conn_pool = psycopg2.pool.ThreadedConnectionPool(minconn=5, maxconn=20, **DB_CONFIG)


# ---------------------------------------------------------------------------------------------
def test_connection():
    """
    Tests the connection to the database for any given connection variable
    :return: connection
    """
    try:
        connection = conn_pool.getconn()
        return connection

    except psycopg2.OperationalError as e:
        print(f"Connection failed. {e}")
        return None


# ---------------------------------------------------------------------------------------------

# --- Creating DataBase Tables ---
conn = test_connection()
if conn is None:
    print("Connection to DataBase failed")
    exit(1)
cursor = conn.cursor()
# Checkpoint
cursor.execute("""
   CREATE TABLE IF NOT EXISTS checkpoint_index
   (
       scheme_code   INT PRIMARY KEY,
       completed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
""")

# Table for Fund Index
cursor.execute("""
        CREATE TABLE IF NOT EXISTS fund_index
        (
            fund_house              VARCHAR,
            scheme_type             VARCHAR,
            scheme_category         VARCHAR,
            scheme_code             INT PRIMARY KEY,
            scheme_name             VARCHAR,
            scheme_start_date       DATE
        )
""")
conn.commit()

# --- Load already completed keys ---
cursor.execute("SELECT scheme_code FROM checkpoint_index")
completed = {str(row[0]) for row in cursor.fetchall()}
remaining_keys = [k for k in keys if k not in completed]
print(f"{len(remaining_keys)}: Scheme Codes Left to be Processed")

cursor.close()
conn_pool.putconn(conn)

# ---------------------------------------------------------------------------------------------

MAX_RETRIES = 5
BASE_DELAY = 0.5


# --- Worker Function to process each fund and load in DataBase
def process_fund(code):
    """
    Processes each Fund Scheme code and loads it into the database
    :param code:
    :return: Success, code
    """

    # worker connection to database
    con = test_connection()
    if con is None:
        return False, code, f"No Connection for Code - Skipping."
    cursor = con.cursor()

    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            time.sleep(random.uniform(0.2, 0.5))
            details = mf.get_scheme_details(code)
            break

        except Exception as e:
            attempts += 1
            if attempts >= MAX_RETRIES:
                return False, code, f"Maximum Retries Reached, Error: {e}"

        time.sleep((BASE_DELAY * (2**attempts - 1)) + random.uniform(0.1, 0.5))

    # get raw data from the API
    try:

        # Validate API response
        if not details or "scheme_start_date" not in details:
            return False, code, f"Invalid API data for code - Skipping"

        dates = details.pop("scheme_start_date")  # get the nested dict inside raw

        try:
            clean_date = datetime.strptime(dates.get("date"), "%d-%m-%Y").strftime(
                "%Y-%m-%d"
            )
        except (ValueError, TypeError):
            # If the API returns 'N/A' or None, insert NULLs into the database
            clean_date = None

        # 2. Explicitly map variables to guarantee exact SQL order
        row = (
            details.get("fund_house"),
            details.get("scheme_type"),
            details.get("scheme_category"),
            int(details.get("scheme_code")),
            details.get("scheme_name"),
            clean_date,
        )

        if not re.search(r"\w", str(details.get("fund_house", ""))):
            return False, code, f"Invalid Entry"

        cursor.execute(
            """
        INSERT INTO fund_index (fund_house, scheme_type, scheme_category, scheme_code, scheme_name, scheme_start_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (scheme_code) DO NOTHING 
        """,
            row,
        )

        # Update the Checkpoint
        # --- Update checkpoint after successful insertion ---
        checkpoint_query = """
                           INSERT INTO checkpoint_index (scheme_code) VALUES (%s) 
                           ON CONFLICT (scheme_code) DO NOTHING 
                           """
        cursor.execute(checkpoint_query, (code,))
        con.commit()
        return True, code, f"Inserted Data"

    except Exception as e:
        con.rollback()
        return False, code, f"Insertion Error: {e}"
    finally:
        cursor.close()
        conn_pool.putconn(con)


try:
    results = thread_map(
        process_fund,
        remaining_keys,
        max_workers=20,
        desc="Logging Indices",
        unit="Funds",
    )

    failed = 0
    # Log the progress in a .jsonl file
    with open("../Data/index_logs.jsonl", "w", newline="\n") as log:

        for success, key, message in results:

            log_record = {
                "timestamp": datetime.now().isoformat(),
                "scheme_code": key,
                "status": "SUCCESS" if success else "FAILED",
                "message": message,
            }

            log.write(json.dumps(log_record) + "\n")

            if not success:
                failed += 1

except Exception as e:
    print(f"Unknown Thread Crash: {e}")

finally:
    print(
        f"Process Completed. Checkpoint Kept for Resumption, Check Logs for Further Info."
    )
    conn_pool.closeall()
