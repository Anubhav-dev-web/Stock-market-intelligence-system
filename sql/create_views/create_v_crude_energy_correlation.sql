CREATE OR REPLACE VIEW analytics.v_crude_energy_correlation AS
WITH crude AS (
    SELECT
        commodity.date_key,
        ROUND(
            (((1 + commodity.daily_return_pct / 100.0) * (1 + fx.daily_return_pct / 100.0)) - 1) * 100,
            4
        ) AS crude_inr_return
    FROM analytics.fct_daily_prices AS commodity
    JOIN analytics.fct_daily_prices AS fx
        ON commodity.date_key = fx.date_key
       AND fx.ticker = 'USDINR=X'
    WHERE commodity.ticker = 'CL=F'
),
energy AS (
    SELECT fact.ticker, companies.company_name, fact.date_key, fact.daily_return_pct
    FROM analytics.fct_daily_prices AS fact
    JOIN analytics.dim_companies AS companies USING (ticker)
    WHERE companies.sector = 'Energy'
)
SELECT
    energy.ticker,
    energy.company_name,
    ROUND(CORR(energy.daily_return_pct, crude.crude_inr_return)::NUMERIC, 3) AS correlation_with_crude_inr,
    COUNT(*) AS trading_days
FROM energy
JOIN crude USING (date_key)
WHERE energy.daily_return_pct IS NOT NULL
GROUP BY energy.ticker, energy.company_name
ORDER BY correlation_with_crude_inr DESC;
