# Walkthrough: SQL Externalization and Pipeline Cleanup

The project now keeps operational SQL in the `sql/` directory and loads it through `pipelines/sql_loader.py`.

## What changed

- The indicator pipeline now uses the SQL files that already existed under `sql/compute_indicators/`
- The daily refresh flow now loads its upsert statement from `sql/daily_refresh/upsert_market_price.sql`
- The analytics view builder now loads view definitions from `sql/create_views/`
- The shared ticker universe moved into `pipelines/market_universe.py`
- The initial `dim_dates` setup no longer depends on the legacy repair script to succeed

## Current SQL layout

```text
sql/
|-- create_everything/
|-- setup_and_load/
|-- setup_dimensions/
|-- fix_dim_dates/
|-- compute_indicators/
|-- create_views/
|-- daily_refresh/
`-- test/
```

## Runtime flow

```bash
python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/test.py
```

For existing databases that were created before the `dim_dates` fix, run:

```bash
python pipelines/fix_dim_dates.py
```
