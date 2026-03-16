SELECT trend_signal, COUNT(*) AS cnt
FROM analytics.fct_daily_prices
GROUP BY trend_signal
ORDER BY cnt DESC
