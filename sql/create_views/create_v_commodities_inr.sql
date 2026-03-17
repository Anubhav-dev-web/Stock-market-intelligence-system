CREATE OR REPLACE VIEW analytics.v_commodities_inr AS
SELECT
    commodity.ticker,
    dates.full_date AS date,
    commodity.close_price AS price_usd,
    fx.close_price AS usdinr_rate,
    ROUND(commodity.close_price * fx.close_price, 2) AS price_inr,
    commodity.daily_return_pct AS usd_return_pct,
    ROUND(
        (((1 + commodity.daily_return_pct / 100.0) * (1 + fx.daily_return_pct / 100.0)) - 1) * 100,
        3
    ) AS inr_return_pct
FROM analytics.fct_daily_prices AS commodity
JOIN analytics.fct_daily_prices AS fx
    ON commodity.date_key = fx.date_key
   AND fx.ticker = 'USDINR=X'
JOIN analytics.dim_dates AS dates
    ON commodity.date_key = dates.date_key
WHERE commodity.ticker IN ('GC=F', 'CL=F', 'SI=F');
