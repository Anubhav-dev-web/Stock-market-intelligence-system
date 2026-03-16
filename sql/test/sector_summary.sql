SELECT sector,
       COUNT(DISTINCT ticker) AS tickers,
       COUNT(*)               AS total_rows,
       MIN(date)              AS earliest,
       MAX(date)              AS latest
FROM raw.market_prices
GROUP BY sector
ORDER BY sector
