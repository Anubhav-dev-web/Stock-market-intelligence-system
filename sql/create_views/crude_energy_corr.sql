CREATE OR REPLACE VIEW analytics.v_crude_energy_correlation AS
WITH crude_returns AS (
    SELECT 
        c.date_key,
        c.daily_return_pct AS crude_return,
        fx.daily_return_pct AS fx_return,
        COALESCE(c.daily_return_pct, 0) + COALESCE(fx.daily_return_pct, 0) AS crude_inr_return
    FROM analytics.fct_daily_prices c
    JOIN analytics.fct_daily_prices fx
        ON c.date_key = fx.date_key
        AND fx.ticker = 'USDINR=X'
    WHERE c.ticker = 'CL=F'
    AND c.daily_return_pct IS NOT NULL
    AND fx.daily_return_pct IS NOT NULL
),
energy_returns AS (
    SELECT 
        f.ticker,
        dc.company_name,
        f.date_key,
        f.daily_return_pct
    FROM analytics.fct_daily_prices f
    JOIN analytics.dim_companies dc USING(ticker)
    WHERE dc.sector = 'Energy'
    AND f.daily_return_pct IS NOT NULL
)
SELECT
    e.ticker,
    e.company_name,
    ROUND(CORR(e.daily_return_pct, c.crude_inr_return)::NUMERIC, 3) 
        AS correlation_with_crude_inr,
    COUNT(*) AS trading_days
FROM energy_returns e
JOIN crude_returns c USING(date_key)
GROUP BY e.ticker, e.company_name
HAVING COUNT(*) > 30
ORDER BY correlation_with_crude_inr DESC NULLS LAST;