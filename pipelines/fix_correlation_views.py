# fix_nan_values.py
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

with engine.connect() as conn:
    # Confirm NaN values exist
    r = conn.execute(text("""
        SELECT COUNT(*) as nan_count
        FROM analytics.fct_daily_prices
        WHERE daily_return_pct::TEXT = 'NaN'
    """))
    print(f"NaN rows in daily_return_pct: {r.scalar()}")

    r = conn.execute(text("""
        SELECT COUNT(*) as nan_count
        FROM analytics.fct_daily_prices
        WHERE weekly_return_pct::TEXT = 'NaN'
    """))
    print(f"NaN rows in weekly_return_pct: {r.scalar()}")

# Fix — replace all NaN with NULL in fct_daily_prices
print("\nFixing NaN values...")
with engine.begin() as conn:
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET daily_return_pct = NULL
        WHERE daily_return_pct::TEXT = 'NaN'
    """))
    print("✓ daily_return_pct NaN → NULL")

    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET weekly_return_pct = NULL
        WHERE weekly_return_pct::TEXT = 'NaN'
    """))
    print("✓ weekly_return_pct NaN → NULL")

    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET monthly_return_pct = NULL
        WHERE monthly_return_pct::TEXT = 'NaN'
    """))
    print("✓ monthly_return_pct NaN → NULL")

    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET rsi_14 = NULL
        WHERE rsi_14::TEXT = 'NaN'
    """))
    print("✓ rsi_14 NaN → NULL")

    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET ma_20 = NULL
        WHERE ma_20::TEXT = 'NaN'
    """))
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET ma_50 = NULL
        WHERE ma_50::TEXT = 'NaN'
    """))
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET ma_200 = NULL
        WHERE ma_200::TEXT = 'NaN'
    """))
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET bb_upper = NULL
        WHERE bb_upper::TEXT = 'NaN'
    """))
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET bb_lower = NULL
        WHERE bb_lower::TEXT = 'NaN'
    """))
    conn.execute(text("""
        UPDATE analytics.fct_daily_prices
        SET pct_from_52w_high = NULL
        WHERE pct_from_52w_high::TEXT = 'NaN'
    """))
    print("✓ All indicator NaN → NULL")

# Now test correlation
with engine.connect() as conn:
    r = conn.execute(text("""
        SELECT 
            CORR(e.daily_return_pct, c.daily_return_pct + fx.daily_return_pct) as corr,
            COUNT(*) as n
        FROM analytics.fct_daily_prices c
        JOIN analytics.fct_daily_prices fx
            ON c.date_key = fx.date_key
            AND fx.ticker = 'USDINR=X'
        JOIN analytics.fct_daily_prices e
            ON c.date_key = e.date_key
        WHERE c.ticker = 'CL=F'
        AND e.ticker = 'ONGC.NS'
        AND c.daily_return_pct IS NOT NULL
        AND fx.daily_return_pct IS NOT NULL
        AND e.daily_return_pct IS NOT NULL
    """))
    row = r.fetchone()
    print(f"\nONGC correlation after fix: {row[0]}")
    print(f"Sample size: {row[1]}")

# Refresh the view
with engine.connect() as conn:
    r = conn.execute(text(
        "SELECT company_name, correlation_with_crude_inr "
        "FROM analytics.v_crude_energy_correlation"
    ))
    print("\n── Final Correlation Results ──")
    for row in r:
        print(f"  {row[0]:<30} {row[1]}")