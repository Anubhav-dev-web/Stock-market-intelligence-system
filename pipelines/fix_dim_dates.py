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


run(load_sql("fix_dim_dates/alter_column_sizes.sql"), "Legacy dim_dates columns updated")
run(load_sql("fix_dim_dates/insert_dim_dates.sql"), "dim_dates synchronized")
run(load_sql("fix_dim_dates/create_fct_daily_prices.sql"), "fct_daily_prices table ensured")

with engine.connect() as conn:
    tables = conn.execute(text(load_sql("fix_dim_dates/verify_tables.sql")))
    print("\nTables")
    for row in tables:
        print(f"  {row[0]}.{row[1]}")

    for table_name, label in [
        ("analytics.dim_companies", "dim_companies"),
        ("analytics.dim_dates", "dim_dates"),
        ("analytics.fct_daily_prices", "fct_daily_prices"),
        ("raw.market_prices", "market_prices"),
    ]:
        row_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        print(f"  {label:<16}: {row_count:,} rows")

print("\nLegacy schema repair complete. Next: python pipelines/compute_indicators.py")
