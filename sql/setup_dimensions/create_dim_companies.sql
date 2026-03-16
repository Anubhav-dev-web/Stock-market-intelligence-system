CREATE TABLE IF NOT EXISTS analytics.dim_companies (
    company_key      SERIAL PRIMARY KEY,
    ticker           VARCHAR(30) UNIQUE NOT NULL,
    company_name     VARCHAR(100),
    sector           VARCHAR(50),
    industry         VARCHAR(100),
    market_cap_tier  VARCHAR(20),
    nifty50_member   BOOLEAN DEFAULT FALSE,
    sensex_member    BOOLEAN DEFAULT FALSE,
    is_commodity     BOOLEAN DEFAULT FALSE,
    is_index         BOOLEAN DEFAULT FALSE,
    currency         VARCHAR(5)  DEFAULT 'INR',
    exchange         VARCHAR(10) DEFAULT 'NSE',
    loaded_at        TIMESTAMP DEFAULT NOW()
);
