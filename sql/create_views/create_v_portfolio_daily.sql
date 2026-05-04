CREATE OR REPLACE VIEW analytics.v_portfolio_daily AS
WITH weights AS (
    SELECT ticker, 0.05 AS weight
    FROM analytics.dim_companies
    WHERE is_index = FALSE
      AND is_commodity = FALSE
    ORDER BY ticker
    LIMIT 20
),
daily AS (
    SELECT
        dates.full_date AS date,
        SUM(fact.daily_return_pct * weights.weight) AS portfolio_return_pct
    FROM analytics.fct_daily_prices AS fact
    JOIN weights USING (ticker)
    JOIN analytics.dim_dates AS dates ON fact.date_key = dates.date_key
    WHERE fact.daily_return_pct IS NOT NULL
      AND fact.daily_return_pct::TEXT <> 'NaN'
    GROUP BY dates.full_date
),
nifty AS (
    SELECT dates.full_date AS date, fact.daily_return_pct AS nifty_return_pct
    FROM analytics.fct_daily_prices AS fact
    JOIN analytics.dim_dates AS dates ON fact.date_key = dates.date_key
    WHERE fact.ticker = '^NSEI'
      AND fact.daily_return_pct IS NOT NULL
      AND fact.daily_return_pct::TEXT <> 'NaN'
)
SELECT
    daily.date,
    ROUND(daily.portfolio_return_pct, 4) AS portfolio_return_pct,
    ROUND(nifty.nifty_return_pct, 4) AS nifty_return_pct,
    ROUND(
        (EXP(SUM(LN(1 + daily.portfolio_return_pct / 100.0)) OVER (ORDER BY daily.date)) - 1) * 100,
        4
    ) AS cumulative_portfolio_pct,
    ROUND(
        (EXP(SUM(LN(1 + nifty.nifty_return_pct / 100.0)) OVER (ORDER BY daily.date)) - 1) * 100,
        4
    ) AS cumulative_nifty_pct
FROM daily
JOIN nifty USING (date)
ORDER BY daily.date;
