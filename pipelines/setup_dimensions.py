import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


def run(sql_text, message):
    with engine.begin() as conn:
        conn.execute(text(sql_text))
    logger.info(message)


run(load_sql("setup_dimensions/create_dim_companies.sql"), "dim_companies table created")
run(load_sql("setup_dimensions/insert_dim_companies.sql"), "dim_companies synchronized")

run(load_sql("setup_dimensions/create_dim_dates.sql"), "dim_dates table created")
run(load_sql("setup_dimensions/insert_dim_dates.sql"), "dim_dates synchronized")

run(load_sql("setup_dimensions/create_fct_daily_prices.sql"), "fct_daily_prices table created")

with engine.connect() as conn:
    tables = conn.execute(text(load_sql("setup_dimensions/verify_tables.sql")))
    print("\nTables in database")
    for row in tables:
        print(f"  {row[0]}.{row[1]}")

    dim_companies_count = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_companies")).scalar()
    dim_dates_count = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_dates")).scalar()
    fact_count = conn.execute(text("SELECT COUNT(*) FROM analytics.fct_daily_prices")).scalar()

print(f"\n  dim_companies    : {dim_companies_count} rows")
print(f"  dim_dates        : {dim_dates_count} rows")
print(f"  fct_daily_prices : {fact_count} rows (empty until indicators run)")
print("\nSetup complete. Next: python pipelines/compute_indicators.py")
print("Legacy databases can still use python pipelines/fix_dim_dates.py if needed.")
