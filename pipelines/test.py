# fix_march_nan.py
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

with engine.begin() as conn:
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET monthly_return_pct = NULL
        WHERE monthly_return_pct::TEXT = 'NaN'
    """))
    print("✓ Fixed NaN in monthly_return_pct")