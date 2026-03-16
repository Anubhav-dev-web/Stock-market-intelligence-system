# setup_dimensions.py
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

# ── 1. dim_companies ──────────────────────────────────────────────────────────
run(load_sql('setup_dimensions/create_dim_companies.sql'), "dim_companies table created")

run(load_sql('setup_dimensions/insert_dim_companies.sql'), "dim_companies populated — 59 instruments")

# ── 2. dim_dates ──────────────────────────────────────────────────────────────
run(load_sql('setup_dimensions/create_dim_dates.sql'), "dim_dates table created")

run(load_sql('setup_dimensions/insert_dim_dates.sql'), "dim_dates populated — 2020 to 2027")

# ── 3. fct_daily_prices ───────────────────────────────────────────────────────
run(load_sql('setup_dimensions/create_fct_daily_prices.sql'), "fct_daily_prices table created")

# ── 4. Verify everything ──────────────────────────────────────────────────────
with engine.connect() as conn:
    r = conn.execute(text(load_sql('setup_dimensions/verify_tables.sql')))
    print("\n── Tables in database ──")
    for row in r:
        print(f"  {row[0]}.{row[1]}")

    r = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_companies"))
    print(f"\n  dim_companies : {r.scalar()} rows")

    r = conn.execute(text("SELECT COUNT(*) FROM analytics.dim_dates"))
    print(f"  dim_dates     : {r.scalar()} rows")

    r = conn.execute(text("SELECT COUNT(*) FROM analytics.fct_daily_prices"))
    print(f"  fct_daily_prices : {r.scalar()} rows (empty — fills next step)")

print("\n✓ Day 2 complete — run: python pipelines/compute_indicators.py")