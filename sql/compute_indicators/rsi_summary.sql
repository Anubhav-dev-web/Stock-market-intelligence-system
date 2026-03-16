SELECT rsi_zone, COUNT(*) AS cnt
FROM analytics.fct_daily_prices
GROUP BY rsi_zone ORDER BY cnt DESC
