SELECT mp.ticker, mp.sector, mp.date,
       mp.open, mp.high, mp.low, mp.close, mp.adj_close, mp.volume,
       dc.company_key
FROM raw.market_prices mp
LEFT JOIN analytics.dim_companies dc USING(ticker)
ORDER BY mp.ticker, mp.date
