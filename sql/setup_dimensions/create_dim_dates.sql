CREATE TABLE IF NOT EXISTS analytics.dim_dates (
    date_key      INTEGER PRIMARY KEY,
    full_date     DATE UNIQUE NOT NULL,
    day_of_week   INTEGER,
    day_name      VARCHAR(10),
    day_of_month  INTEGER,
    week_number   INTEGER,
    month_number  INTEGER,
    month_name    VARCHAR(10),
    quarter       INTEGER,
    year          INTEGER,
    is_weekend    BOOLEAN,
    fy_year       VARCHAR(10),
    fy_quarter    VARCHAR(10)
);
