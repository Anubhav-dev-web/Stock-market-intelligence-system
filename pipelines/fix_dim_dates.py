# fix_dim_dates.py
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os, logging
from sql_loader import load_sql

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

def run(sql, msg):
    with engine.begin() as conn:
        conn.execute(text(sql))
    logger.info(f"✓ {msg}")

# Fix column sizes
run(load_sql('fix_dim_dates/alter_column_sizes.sql'), "Column sizes fixed")

# Now populate dim_dates
run(load_sql('fix_dim_dates/insert_dim_dates.sql'), "dim_dates populated — 2922 rows")

# Create fct_daily_prices
run(load_sql('fix_dim_dates/create_fct_daily_prices.sql'), "fct_daily_prices table created")

# Verify
with engine.connect() as conn:
    r = conn.execute(text(load_sql('fix_dim_dates/verify_tables.sql')))
    print("\n── Tables ──")
    for row in r:
        print(f"  {row[0]}.{row[1]}")

    for tbl, label in [
        ("analytics.dim_companies",    "dim_companies   "),
        ("analytics.dim_dates",        "dim_dates       "),
        ("analytics.fct_daily_prices", "fct_daily_prices"),
        ("raw.market_prices",          "market_prices   "),
    ]:
        r = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
        print(f"  {label}: {r.scalar():,} rows")

print("\n✓ Day 2 complete — run: python pipelines/compute_indicators.py")