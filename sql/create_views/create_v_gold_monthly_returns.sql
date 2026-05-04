CREATE OR REPLACE VIEW analytics.v_gold_monthly_returns AS
WITH gold_daily AS (
    SELECT
        fact.ticker,
        dates.year,
        dates.month_number,
        dates.month_name,
        dates.full_date,
        fact.close_price,
        fact.monthly_return_pct AS rolling_21d_return_pct
    FROM analytics.fct_daily_prices fact
    JOIN analytics.dim_dates dates
        ON dates.date_key = fact.date_key
    WHERE fact.ticker = 'GC=F'
      AND fact.close_price IS NOT NULL
),
month_bounds AS (
    SELECT DISTINCT
        ticker,
        year,
        month_number,
        month_name,
        FIRST_VALUE(full_date) OVER month_window AS first_trade_date,
        LAST_VALUE(full_date) OVER month_window AS last_trade_date,
        FIRST_VALUE(close_price) OVER month_window AS first_close_price,
        LAST_VALUE(close_price) OVER month_window AS last_close_price,
        COUNT(*) OVER month_window AS trading_days,
        AVG(rolling_21d_return_pct) OVER month_window AS avg_rolling_21d_return_pct,
        COUNT(rolling_21d_return_pct) OVER month_window AS rolling_21d_non_null_days
    FROM gold_daily
    WINDOW month_window AS (
        PARTITION BY ticker, year, month_number, month_name
        ORDER BY full_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
)
SELECT
    ticker,
    year,
    month_number,
    month_name,
    first_trade_date,
    last_trade_date,
    trading_days,
    ROUND((((last_close_price / NULLIF(first_close_price, 0)) - 1) * 100)::NUMERIC, 4)
        AS calendar_month_return_pct,
    ROUND(avg_rolling_21d_return_pct::NUMERIC, 4) AS avg_rolling_21d_return_pct,
    rolling_21d_non_null_days
FROM month_bounds;
