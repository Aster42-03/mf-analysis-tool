from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from datetime import datetime
from mftool import Mftool
import psycopg2
import time
import os

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


def test_connection():
    """
    Tests the connection to the database for any given connection variable
    :return: connection
    """
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection

    except psycopg2.OperationalError as e:
        print(f"Connection failed. {e}")
        return None


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
       scheme_code   TEXT PRIMARY KEY,
       completed_at  TEXT
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
            scheme_start_date       DATE,
            nav                     REAL
        )
""")
conn.commit()

# --- Load already completed keys ---
cursor.execute("SELECT scheme_code FROM checkpoint")
completed = {row[0] for row in cursor.fetchall()}
remaining_keys = [k for k in keys if k not in completed]
print(f"{len(remaining_keys)}: Scheme Codes Left to be Processed")

cursor.close()
conn.close()


# --- Worker Function to process each fund and load in DataBase
def process_fund(code):
    """
    Processes each fund scheme code and loads it into the database
    :param code:
    :return: Success, code
    """

    # managing api request limit
    time.sleep(0.5)

    # console message
    print(f"Currently Processing Code: {code}")

    # worker connection to database
    con = test_connection()
    if con is None:
        print(f"No Connection for Code: {code} - Skipping.")
        return False, code
    cursor = con.cursor()

    # get raw data from the API
    try:
        details = mf.get_scheme_details(code)
        # Validate API response
        if not details or "scheme_start_date" not in details:
            print(f"Invalid API data for code: {code} - Skipping")
            return False, code
        dates = details.pop("scheme_start_date")  # get the nested dict inside raw

        # 2. Explicitly map variables to guarantee exact SQL order
        row = (
            details.get("fund_house"),
            details.get("scheme_type"),
            details.get("scheme_category"),
            details.get("scheme_code"),
            details.get("scheme_name"),
            dates.get("date"),
            dates.get("nav"),
        )

        cursor.execute(
            """
        INSERT INTO fund_index (fund_house, scheme_type, scheme_category, scheme_code, scheme_name, scheme_start_date, nav)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scheme_code) DO NOTHING 
        """,
            row,
        )
        print(f" -> Successfully Inserted Data for Code: {code}")

        # Update the Checkpoint
        # --- Update checkpoint after successful insertion ---
        checkpoint_query = """
                           INSERT INTO checkpoint (scheme_code, completed_at)
                           VALUES (%s, %s) 
                           ON CONFLICT (scheme_code) DO NOTHING 
                           """
        cursor.execute(checkpoint_query, (code, datetime.now().isoformat()))
        con.commit()
        return True, code

    except Exception as e:
        print(f"Insertion error: {e}")
        con.rollback()
        return False, code
    finally:
        cursor.close()
        con.close()


with ThreadPoolExecutor(max_workers=3) as executor:
    result = executor.map(process_fund, remaining_keys)
    failed = 0
    for success, k in result:
        if not success:
            failed += 1
    print(f"Process Completed. {failed} Codes Failed, Checkpoint Kept for Resumption")
