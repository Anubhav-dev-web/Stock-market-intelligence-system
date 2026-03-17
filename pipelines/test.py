import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from sql_loader import load_sql

load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

with engine.connect() as conn:
    result = conn.execute(text(load_sql("test/sector_summary.sql")))
    print(f"\n{'Sector':<12} {'Tickers':>8} {'Rows':>10} {'From':>12} {'To':>12}")
    print("-" * 58)
    for row in result:
        print(f"{row[0]:<12} {row[1]:>8} {row[2]:>10,} {str(row[3]):>12} {str(row[4]):>12}")
