from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

sql = """
CREATE OR REPLACE VIEW analytics.v_sector_correlation AS
WITH latest_30d AS (
    SELECT 
        f.date_key,
        dc.sector,
        AVG(f.daily_return_pct) as avg_return
    FROM analytics.fct_daily_prices f
    JOIN analytics.dim_companies dc USING(ticker)
    WHERE dc.is_index = FALSE
    AND dc.is_commodity = FALSE
    AND dc.sector NOT IN ('Forex')
    AND f.daily_return_pct IS NOT NULL
    AND f.date_key >= (
        SELECT MAX(date_key) - 3000 
        FROM analytics.fct_daily_prices
    )
    GROUP BY f.date_key, dc.sector
),
it     AS (SELECT date_key, avg_return FROM latest_30d WHERE sector = 'IT'),
bank   AS (SELECT date_key, avg_return FROM latest_30d WHERE sector = 'Banking'),
pharma AS (SELECT date_key, avg_return FROM latest_30d WHERE sector = 'Pharma'),
energy AS (SELECT date_key, avg_return FROM latest_30d WHERE sector = 'Energy'),
fmcg   AS (SELECT date_key, avg_return FROM latest_30d WHERE sector = 'FMCG')

SELECT
    'IT'     AS sector_1, 'IT'     AS sector_2, ROUND(CORR(i.avg_return::FLOAT8, i.avg_return::FLOAT8)::NUMERIC, 2) AS correlation FROM it i JOIN it i2 ON i.date_key = i2.date_key
UNION ALL
SELECT 'IT', 'Banking',  ROUND(CORR(i.avg_return::FLOAT8, b.avg_return::FLOAT8)::NUMERIC, 2) FROM it i JOIN bank b ON i.date_key = b.date_key
UNION ALL
SELECT 'IT', 'Pharma',   ROUND(CORR(i.avg_return::FLOAT8, p.avg_return::FLOAT8)::NUMERIC, 2) FROM it i JOIN pharma p ON i.date_key = p.date_key
UNION ALL
SELECT 'IT', 'Energy',   ROUND(CORR(i.avg_return::FLOAT8, e.avg_return::FLOAT8)::NUMERIC, 2) FROM it i JOIN energy e ON i.date_key = e.date_key
UNION ALL
SELECT 'IT', 'FMCG',     ROUND(CORR(i.avg_return::FLOAT8, f.avg_return::FLOAT8)::NUMERIC, 2) FROM it i JOIN fmcg f ON i.date_key = f.date_key
UNION ALL
SELECT 'Banking', 'IT',      ROUND(CORR(b.avg_return::FLOAT8, i.avg_return::FLOAT8)::NUMERIC, 2) FROM bank b JOIN it i ON b.date_key = i.date_key
UNION ALL
SELECT 'Banking', 'Banking', ROUND(CORR(b.avg_return::FLOAT8, b.avg_return::FLOAT8)::NUMERIC, 2) FROM bank b JOIN bank b2 ON b.date_key = b2.date_key
UNION ALL
SELECT 'Banking', 'Pharma',  ROUND(CORR(b.avg_return::FLOAT8, p.avg_return::FLOAT8)::NUMERIC, 2) FROM bank b JOIN pharma p ON b.date_key = p.date_key
UNION ALL
SELECT 'Banking', 'Energy',  ROUND(CORR(b.avg_return::FLOAT8, e.avg_return::FLOAT8)::NUMERIC, 2) FROM bank b JOIN energy e ON b.date_key = e.date_key
UNION ALL
SELECT 'Banking', 'FMCG',    ROUND(CORR(b.avg_return::FLOAT8, f.avg_return::FLOAT8)::NUMERIC, 2) FROM bank b JOIN fmcg f ON b.date_key = f.date_key
UNION ALL
SELECT 'Pharma', 'IT',      ROUND(CORR(p.avg_return::FLOAT8, i.avg_return::FLOAT8)::NUMERIC, 2) FROM pharma p JOIN it i ON p.date_key = i.date_key
UNION ALL
SELECT 'Pharma', 'Banking', ROUND(CORR(p.avg_return::FLOAT8, b.avg_return::FLOAT8)::NUMERIC, 2) FROM pharma p JOIN bank b ON p.date_key = b.date_key
UNION ALL
SELECT 'Pharma', 'Pharma',  ROUND(CORR(p.avg_return::FLOAT8, p.avg_return::FLOAT8)::NUMERIC, 2) FROM pharma p JOIN pharma p2 ON p.date_key = p2.date_key
UNION ALL
SELECT 'Pharma', 'Energy',  ROUND(CORR(p.avg_return::FLOAT8, e.avg_return::FLOAT8)::NUMERIC, 2) FROM pharma p JOIN energy e ON p.date_key = e.date_key
UNION ALL
SELECT 'Pharma', 'FMCG',    ROUND(CORR(p.avg_return::FLOAT8, f.avg_return::FLOAT8)::NUMERIC, 2) FROM pharma p JOIN fmcg f ON p.date_key = f.date_key
UNION ALL
SELECT 'Energy', 'IT',      ROUND(CORR(e.avg_return::FLOAT8, i.avg_return::FLOAT8)::NUMERIC, 2) FROM energy e JOIN it i ON e.date_key = i.date_key
UNION ALL
SELECT 'Energy', 'Banking', ROUND(CORR(e.avg_return::FLOAT8, b.avg_return::FLOAT8)::NUMERIC, 2) FROM energy e JOIN bank b ON e.date_key = b.date_key
UNION ALL
SELECT 'Energy', 'Pharma',  ROUND(CORR(e.avg_return::FLOAT8, p.avg_return::FLOAT8)::NUMERIC, 2) FROM energy e JOIN pharma p ON e.date_key = p.date_key
UNION ALL
SELECT 'Energy', 'Energy',  ROUND(CORR(e.avg_return::FLOAT8, e.avg_return::FLOAT8)::NUMERIC, 2) FROM energy e JOIN energy e2 ON e.date_key = e2.date_key
UNION ALL
SELECT 'Energy', 'FMCG',    ROUND(CORR(e.avg_return::FLOAT8, f.avg_return::FLOAT8)::NUMERIC, 2) FROM energy e JOIN fmcg f ON e.date_key = f.date_key
UNION ALL
SELECT 'FMCG', 'IT',      ROUND(CORR(f.avg_return::FLOAT8, i.avg_return::FLOAT8)::NUMERIC, 2) FROM fmcg f JOIN it i ON f.date_key = i.date_key
UNION ALL
SELECT 'FMCG', 'Banking', ROUND(CORR(f.avg_return::FLOAT8, b.avg_return::FLOAT8)::NUMERIC, 2) FROM fmcg f JOIN bank b ON f.date_key = b.date_key
UNION ALL
SELECT 'FMCG', 'Pharma',  ROUND(CORR(f.avg_return::FLOAT8, p.avg_return::FLOAT8)::NUMERIC, 2) FROM fmcg f JOIN pharma p ON f.date_key = p.date_key
UNION ALL
SELECT 'FMCG', 'Energy',  ROUND(CORR(f.avg_return::FLOAT8, e.avg_return::FLOAT8)::NUMERIC, 2) FROM fmcg f JOIN energy e ON f.date_key = e.date_key
UNION ALL
SELECT 'FMCG', 'FMCG',    ROUND(CORR(f.avg_return::FLOAT8, f.avg_return::FLOAT8)::NUMERIC, 2) FROM fmcg f JOIN fmcg f2 ON f.date_key = f2.date_key;
"""

with engine.begin() as conn:
    conn.execute(text(sql))
    print("✓ View created")

with engine.connect() as conn:
    r = conn.execute(text("SELECT * FROM analytics.v_sector_correlation ORDER BY sector_1, sector_2"))
    print(f"\n{'Sector 1':<12} {'Sector 2':<12} {'Correlation':>12}")
    print("-" * 38)
    for row in r:
        print(f"{row[0]:<12} {row[1]:<12} {float(row[2]) if row[2] else 'NaN':>12}")