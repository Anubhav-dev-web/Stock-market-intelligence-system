ALTER TABLE analytics.dim_dates
    ALTER COLUMN day_name   TYPE VARCHAR(20),
    ALTER COLUMN month_name TYPE VARCHAR(20),
    ALTER COLUMN fy_year    TYPE VARCHAR(20),
    ALTER COLUMN fy_quarter TYPE VARCHAR(20);
