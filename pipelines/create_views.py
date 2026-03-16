# pipelines/create_views.py
import sys, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

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

# ── View 1: Commodities in INR ────────────────────────────────────────────────
run("""
CREATE OR REPLACE VIEW analytics.v_commodities_inr AS
SELECT
    c.ticker,
    d.full_date                                      AS date,
    c.close_price                                    AS price_usd,
    fx.close_price                                   AS usdinr_rate,
    ROUND(c.close_price * fx.close_price, 2)         AS price_inr,
    c.daily_return_pct                               AS usd_return_pct,
    ROUND(c.daily_return_pct + fx.daily_return_pct, 3) AS inr_return_pct
FROM analytics.fct_daily_prices c
JOIN analytics.fct_daily_prices fx
    ON  c.date_key = fx.date_key
    AND fx.ticker  = 'USDINR=X'
JOIN analytics.dim_dates d
    ON  c.date_key = d.date_key
WHERE c.ticker IN ('GC=F','CL=F','SI=F');
""", "v_commodities_inr created")

# ── View 2: Sector Performance ────────────────────────────────────────────────
run("""
CREATE OR REPLACE VIEW analytics.v_sector_performance AS
SELECT
    dc.sector,
    COUNT(DISTINCT f.ticker)                                       AS num_stocks,
    ROUND(AVG(f.daily_return_pct),   2)                           AS avg_return_1d,
    ROUND(AVG(f.weekly_return_pct),  2)                           AS avg_return_1w,
    ROUND(AVG(f.monthly_return_pct), 2)                           AS avg_return_1m,
    ROUND(AVG(f.rsi_14), 1)                                       AS avg_rsi,
    COUNT(CASE WHEN f.rsi_zone     = 'Overbought'    THEN 1 END)  AS overbought_count,
    COUNT(CASE WHEN f.rsi_zone     = 'Oversold'      THEN 1 END)  AS oversold_count,
    COUNT(CASE WHEN f.trend_signal LIKE '%Bullish%'  THEN 1 END)  AS bullish_count,
    COUNT(CASE WHEN f.trend_signal LIKE '%Bearish%'  THEN 1 END)  AS bearish_count,
    MAX(d.full_date)                                               AS as_of_date
FROM analytics.fct_daily_prices f
JOIN analytics.dim_companies dc USING(ticker)
JOIN analytics.dim_dates      d  ON f.date_key = d.date_key
WHERE dc.is_index     = FALSE
  AND dc.is_commodity = FALSE
  AND d.full_date = (
      SELECT MAX(dd.full_date)
      FROM analytics.fct_daily_prices ff
      JOIN analytics.dim_dates dd ON ff.date_key = dd.date_key
      WHERE ff.ticker = 'TCS.NS'
  )
GROUP BY dc.sector;
""", "v_sector_performance created")

# ── View 3: Crude Oil vs Energy Correlation ───────────────────────────────────
run("""
CREATE OR REPLACE VIEW analytics.v_crude_energy_correlation AS
WITH crude AS (
    SELECT
        c.date_key,
        ROUND(c.daily_return_pct + fx.daily_return_pct, 4) AS crude_inr_return
    FROM analytics.fct_daily_prices c
    JOIN analytics.fct_daily_prices fx
        ON  c.date_key = fx.date_key
        AND fx.ticker  = 'USDINR=X'
    WHERE c.ticker = 'CL=F'
),
energy AS (
    SELECT f.ticker, dc.company_name, f.date_key, f.daily_return_pct
    FROM analytics.fct_daily_prices f
    JOIN analytics.dim_companies dc USING(ticker)
    WHERE dc.sector = 'Energy'
)
SELECT
    e.ticker,
    e.company_name,
    ROUND(CORR(e.daily_return_pct, c.crude_inr_return)::NUMERIC, 3)
        AS correlation_with_crude_inr,
    COUNT(*) AS trading_days
FROM energy e
JOIN crude  c USING(date_key)
WHERE e.daily_return_pct IS NOT NULL
GROUP BY e.ticker, e.company_name
ORDER BY correlation_with_crude_inr DESC;
""", "v_crude_energy_correlation created")

# ── View 4: Portfolio vs NIFTY ────────────────────────────────────────────────
run("""
CREATE OR REPLACE VIEW analytics.v_portfolio_daily AS
WITH weights AS (
    SELECT ticker, 0.05 AS weight
    FROM analytics.dim_companies
    WHERE is_index     = FALSE
      AND is_commodity = FALSE
      AND sector NOT IN ('Forex')
    LIMIT 20
),
daily AS (
    SELECT
        d.full_date                              AS date,
        SUM(f.daily_return_pct * w.weight)       AS portfolio_return_pct
    FROM analytics.fct_daily_prices f
    JOIN weights                 w  USING(ticker)
    JOIN analytics.dim_dates     d  ON f.date_key = d.date_key
    WHERE f.daily_return_pct IS NOT NULL
    GROUP BY d.full_date
),
nifty AS (
    SELECT d.full_date AS date, f.daily_return_pct AS nifty_return
    FROM analytics.fct_daily_prices f
    JOIN analytics.dim_dates d ON f.date_key = d.date_key
    WHERE f.ticker = '^NSEI'
)
SELECT
    p.date,
    ROUND(p.portfolio_return_pct, 4)         AS portfolio_return_pct,
    ROUND(n.nifty_return, 4)                 AS nifty_return_pct,
    ROUND(SUM(p.portfolio_return_pct)
          OVER (ORDER BY p.date), 4)         AS cumulative_portfolio_pct,
    ROUND(SUM(n.nifty_return)
          OVER (ORDER BY p.date), 4)         AS cumulative_nifty_pct
FROM daily p
JOIN nifty n USING(date)
ORDER BY p.date;
""", "v_portfolio_daily created")

# ── Verify all views ──────────────────────────────────────────────────────────
with engine.connect() as conn:
    r = conn.execute(text("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'analytics'
        ORDER BY table_name
    """))
    views = [row[0] for row in r]
    print(f"\n── Analytics views ({len(views)}) ──")
    for v in views:
        print(f"  ✓ {v}")

    # Quick sanity check on each view
    for view in views:
        try:
            r = conn.execute(text(
                f"SELECT COUNT(*) FROM analytics.{view}"
            ))
            print(f"    rows: {r.scalar():,}")
        except Exception as e:
            print(f"    ✗ {e}")

print("\n✓ All views ready — Day 3 fully complete")
print("  Next: python pipelines/daily_refresh.py  (Day 4)")