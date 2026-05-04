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

VIEW_DEFINITIONS = [
    ("create_views/create_v_commodities_inr.sql", "analytics.v_commodities_inr"),
    ("create_views/create_v_gold_monthly_returns.sql", "analytics.v_gold_monthly_returns"),
    ("create_views/create_v_sector_performance.sql", "analytics.v_sector_performance"),
    ("create_views/create_v_crude_energy_correlation.sql", "analytics.v_crude_energy_correlation"),
    ("create_views/create_v_portfolio_daily.sql", "analytics.v_portfolio_daily"),
]


def run(relative_path, view_name):
    with engine.begin() as conn:
        conn.execute(text(load_sql(relative_path)))
    logger.info("%s created", view_name)


for relative_path, view_name in VIEW_DEFINITIONS:
    run(relative_path, view_name)

with engine.connect() as conn:
    views = [row[0] for row in conn.execute(text(load_sql("create_views/list_views.sql")))]
    print(f"\nAnalytics views ({len(views)})")
    for view in views:
        row_count = conn.execute(text(f"SELECT COUNT(*) FROM analytics.{view}")).scalar()
        print(f"  {view:<32} {row_count:,} rows")

print("\nAll views are ready.")
print("Next: python pipelines/daily_refresh.py")
