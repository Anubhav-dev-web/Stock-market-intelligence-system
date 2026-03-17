CREATE OR REPLACE VIEW analytics.v_sector_performance AS
WITH latest_date AS (
    SELECT MAX(dates.full_date) AS full_date
    FROM analytics.fct_daily_prices AS fact
    JOIN analytics.dim_companies AS companies USING (ticker)
    JOIN analytics.dim_dates AS dates ON fact.date_key = dates.date_key
    WHERE companies.is_index = FALSE
      AND companies.is_commodity = FALSE
)
SELECT
    companies.sector,
    COUNT(DISTINCT fact.ticker) AS num_stocks,
    ROUND(AVG(fact.daily_return_pct), 2) AS avg_return_1d,
    ROUND(AVG(fact.weekly_return_pct), 2) AS avg_return_1w,
    ROUND(AVG(fact.monthly_return_pct), 2) AS avg_return_1m,
    ROUND(AVG(fact.rsi_14), 1) AS avg_rsi,
    COUNT(CASE WHEN fact.rsi_zone = 'Overbought' THEN 1 END) AS overbought_count,
    COUNT(CASE WHEN fact.rsi_zone = 'Oversold' THEN 1 END) AS oversold_count,
    COUNT(CASE WHEN fact.trend_signal LIKE '%Bullish%' THEN 1 END) AS bullish_count,
    COUNT(CASE WHEN fact.trend_signal LIKE '%Bearish%' THEN 1 END) AS bearish_count,
    MAX(dates.full_date) AS as_of_date
FROM analytics.fct_daily_prices AS fact
JOIN analytics.dim_companies AS companies USING (ticker)
JOIN analytics.dim_dates AS dates ON fact.date_key = dates.date_key
JOIN latest_date ON dates.full_date = latest_date.full_date
WHERE companies.is_index = FALSE
  AND companies.is_commodity = FALSE
GROUP BY companies.sector;
