INSERT INTO raw.market_prices
    (ticker, sector, date, open, high, low, close, adj_close, volume, loaded_at)
VALUES
    (:ticker, :sector, :date, :open, :high, :low, :close, :adj_close, :volume, :loaded_at)
ON CONFLICT (ticker, date) DO UPDATE SET
    sector = EXCLUDED.sector,
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    adj_close = EXCLUDED.adj_close,
    volume = EXCLUDED.volume,
    loaded_at = EXCLUDED.loaded_at;
