INSERT INTO analytics.dim_dates
SELECT
    TO_CHAR(d,'YYYYMMDD')::INTEGER                        AS date_key,
    d                                                      AS full_date,
    EXTRACT(ISODOW FROM d)                                AS day_of_week,
    TRIM(TO_CHAR(d,'Day'))                                AS day_name,
    EXTRACT(DAY FROM d)                                   AS day_of_month,
    EXTRACT(WEEK FROM d)                                  AS week_number,
    EXTRACT(MONTH FROM d)                                 AS month_number,
    TRIM(TO_CHAR(d,'Month'))                              AS month_name,
    EXTRACT(QUARTER FROM d)                               AS quarter,
    EXTRACT(YEAR FROM d)                                  AS year,
    EXTRACT(ISODOW FROM d) IN (6,7)                      AS is_weekend,
    CASE
        WHEN EXTRACT(MONTH FROM d) >= 4
        THEN 'FY' || EXTRACT(YEAR FROM d)::INT
             || '-' || (EXTRACT(YEAR FROM d)::INT + 1)
        ELSE 'FY' || (EXTRACT(YEAR FROM d)::INT - 1)
             || '-' || EXTRACT(YEAR FROM d)::INT
    END                                                   AS fy_year,
    CASE
        WHEN EXTRACT(MONTH FROM d) BETWEEN 4  AND 6  THEN 'Q1'
        WHEN EXTRACT(MONTH FROM d) BETWEEN 7  AND 9  THEN 'Q2'
        WHEN EXTRACT(MONTH FROM d) BETWEEN 10 AND 12 THEN 'Q3'
        ELSE 'Q4'
    END                                                   AS fy_quarter
FROM GENERATE_SERIES('2020-01-01'::DATE,
                     '2027-12-31'::DATE,
                     '1 day'::INTERVAL) AS d
ON CONFLICT (date_key) DO NOTHING;
