INSERT INTO raw.market_prices
    (ticker, sector, date, open, high, low,
     close, adj_close, volume, loaded_at)
VALUES
    (:ticker, :sector, :date, :open, :high, :low,
     :close, :adj_close, :volume, :loaded_at)
ON CONFLICT (ticker, date) DO NOTHING
