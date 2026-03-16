SELECT sector,
       COUNT(DISTINCT ticker) AS tickers,
       COUNT(*)               AS rows,
       MIN(date)              AS from_date,
       MAX(date)              AS to_date
FROM raw.market_prices
GROUP BY sector
ORDER BY sector
