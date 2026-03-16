CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.market_prices (
    id          BIGSERIAL PRIMARY KEY,
    ticker      VARCHAR(30)   NOT NULL,
    sector      VARCHAR(50),
    date        DATE          NOT NULL,
    open        NUMERIC(12,4),
    high        NUMERIC(12,4),
    low         NUMERIC(12,4),
    close       NUMERIC(12,4),
    adj_close   NUMERIC(12,4),
    volume      BIGINT,
    loaded_at   TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_ticker_date UNIQUE (ticker, date)
);
