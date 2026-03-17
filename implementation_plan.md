# Implementation Plan

## Completed fixes

### Pipeline correctness

- `pipelines/compute_indicators.py`
  - Uses the `sql/compute_indicators/` queries
  - Includes `adj_close` in the fact load
  - Truncates `analytics.fct_daily_prices` before reload
  - Prints fact-table trend and RSI summaries after refresh

- `pipelines/setup_dimensions.py`
  - Works with the corrected `dim_dates` schema on first run

- `pipelines/fix_dim_dates.py`
  - Synchronizes existing date rows instead of only inserting missing keys

### Shared configuration

- Added `pipelines/market_universe.py` so the historical load and daily refresh use one ticker definition

### SQL organization

- Added `sql/daily_refresh/upsert_market_price.sql`
- Added `sql/create_views/` for analytics view definitions
- Added indexes to `sql/setup_and_load/create_schema.sql`

### Orchestration

- `airflow_dags/india_market_dag.py` now uses environment-aware project and Python paths instead of hardcoded machine-specific values

### Documentation

- Corrected the command name to `compute_indicators.py`
- Restored and updated `README.md` to match the current project state
