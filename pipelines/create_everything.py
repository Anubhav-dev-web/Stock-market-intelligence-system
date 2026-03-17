import os

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text

from sql_loader import load_sql

load_dotenv()

USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
TARGET_DB = os.getenv("DB_NAME", "india_market")

print(f"Step 1: Creating '{TARGET_DB}' database...")
try:
    conn = psycopg2.connect(
        dbname="postgres",
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute(load_sql("create_everything/check_db_exists.sql"), {"db_name": TARGET_DB})
    exists = cur.fetchone()

    if exists:
        print(f"  Database '{TARGET_DB}' already exists")
    else:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TARGET_DB)))
        print(f"  Database '{TARGET_DB}' created")

    cur.close()
    conn.close()
except Exception as exc:
    print(f"  Failed to create database: {exc}")
    raise

print("\nStep 2: Creating schemas and tables...")
engine = create_engine(f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{TARGET_DB}")

with engine.begin() as conn:
    conn.execute(text(load_sql("create_everything/create_schemas_and_table.sql")))
print("  Schemas created: raw, staging, analytics")
print("  Table created:   raw.market_prices")

print("\nStep 3: Verifying...")
with engine.connect() as conn:
    schemas = [row[0] for row in conn.execute(text(load_sql("create_everything/verify_schemas.sql")))]
    tables = [row[0] for row in conn.execute(text(load_sql("create_everything/verify_tables.sql")))]
    row_count = conn.execute(text(load_sql("create_everything/count_market_prices.sql"))).scalar()

print(f"  Schemas: {schemas}")
print(f"  Tables:  {tables}")
print(f"  Rows:    {row_count} (empty and ready to load)")
print("\nAll done. Next: python pipelines/setup_and_load.py")
