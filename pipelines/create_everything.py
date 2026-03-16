# create_everything.py
# Connects to 'postgres' default DB first, creates 'india_market', then builds schema

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from sql_loader import load_sql

load_dotenv()

USER = os.getenv('DB_USER')
PASS = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')

# ── STEP 1: Create the database itself ───────────────────────────────────────
# Must connect to 'postgres' default DB to create a new database
print("Step 1: Creating 'india_market' database...")
try:
    conn = psycopg2.connect(
        dbname   = 'postgres',   # connect to default DB
        user     = USER,
        password = PASS,
        host     = HOST,
        port     = PORT
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if database already exists
    cur.execute(load_sql('create_everything/check_db_exists.sql'))
    exists = cur.fetchone()

    if exists:
        print("  ✓ Database 'india_market' already exists")
    else:
        cur.execute("CREATE DATABASE india_market")
        print("  ✓ Database 'india_market' CREATED")

    cur.close()
    conn.close()

except Exception as e:
    print(f"  ✗ Failed to create database: {e}")
    raise

# ── STEP 2: Now connect to india_market and create schemas + table ────────────
print("\nStep 2: Creating schemas and tables...")
engine = create_engine(
    f"postgresql://{USER}:{PASS}@{HOST}:{PORT}/india_market"
)

with engine.begin() as conn:
    conn.execute(text(load_sql('create_everything/create_schemas_and_table.sql')))
print("  ✓ Schemas created: raw, staging, analytics")
print("  ✓ Table created:   raw.market_prices")

# ── STEP 3: Verify everything ─────────────────────────────────────────────────
print("\nStep 3: Verifying...")
with engine.connect() as conn:
    r = conn.execute(text(load_sql('create_everything/verify_schemas.sql')))
    schemas = [row[0] for row in r]
    print(f"  Schemas: {schemas}")

    r = conn.execute(text(load_sql('create_everything/verify_tables.sql')))
    tables = [row[0] for row in r]
    print(f"  Tables:  {tables}")

    r = conn.execute(text(load_sql('create_everything/count_market_prices.sql')))
    print(f"  Rows:    {r.scalar()} (empty — ready to load)")

print("\n✓ ALL DONE — now run: python setup_and_load.py")