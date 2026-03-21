# Stock Market Intelligence System

A Python and PostgreSQL ETL pipeline that ingests Indian market data from Yahoo Finance, models it into a star schema, computes technical indicators, and publishes analytics views for downstream reporting.

For a complete setup, execution, and code walkthrough, see `end_to_end_guide.md`.
For a compact implementation and troubleshooting handoff, see `project_journal.md`.

## What the project does

- Loads raw OHLCV data for 59 instruments into `raw.market_prices`
- Builds `analytics.dim_companies` and `analytics.dim_dates`
- Computes indicator-enriched rows into `analytics.fct_daily_prices`
- Creates reusable analytics views for sector performance, commodity pricing in INR, and benchmark comparisons
- Supports both an initial historical load and a daily refresh flow

## Tech stack

- Python 3.x
- PostgreSQL
- SQLAlchemy
- psycopg2
- pandas
- yfinance
- python-dotenv
- Apache Airflow for orchestration

## Project structure

```text
MKT-1/
|-- airflow_dags/
|   `-- india_market_dag.py
|-- data/
|-- dbt_projects/
|-- notebooks/
|-- pipelines/
|   |-- create_everything.py
|   |-- setup_and_load.py
|   |-- setup_dimensions.py
|   |-- fix_dim_dates.py
|   |-- compute_indicators.py
|   |-- create_views.py
|   |-- daily_refresh.py
|   |-- market_universe.py
|   |-- sql_loader.py
|   `-- test.py
|-- sql/
|   |-- create_everything/
|   |-- setup_and_load/
|   |-- setup_dimensions/
|   |-- fix_dim_dates/
|   |-- compute_indicators/
|   |-- create_views/
|   |-- daily_refresh/
|   `-- test/
|-- .env
|-- .gitignore
`-- requirements.txt
```

## Data model

### Raw

- `raw.market_prices`: market OHLCV data with a unique key on `(ticker, date)`

### Analytics

- `analytics.dim_companies`: static metadata for stocks, commodities, and indices
- `analytics.dim_dates`: calendar dimension with fiscal year and fiscal quarter values
- `analytics.fct_daily_prices`: enriched price fact table with returns, moving averages, Bollinger Bands, RSI, and 52-week range metrics

## Pipeline flow

### 1. Bootstrap the database

```bash
python pipelines/create_everything.py
```

Creates the target database from `.env`, then builds the `raw`, `staging`, and `analytics` schemas and the `raw.market_prices` table.

### 2. Load historical data

```bash
python pipelines/setup_and_load.py
```

Fetches roughly two years of history for the full market universe and inserts rows into `raw.market_prices`.

### 3. Build dimensions and fact table shell

```bash
python pipelines/setup_dimensions.py
```

Creates and populates `dim_companies` and `dim_dates`, then creates `fct_daily_prices`.

### 4. Repair older databases if needed

```bash
python pipelines/fix_dim_dates.py
```

Optional. This keeps older databases aligned with the current `dim_dates` shape and values.

### 5. Compute indicators

```bash
python pipelines/compute_indicators.py
```

Loads raw prices, recalculates indicators, truncates the fact table, and reloads it safely for reruns.

### 6. Create analytics views

```bash
python pipelines/create_views.py
```

Builds the reporting views in the `analytics` schema.

### 7. Run a daily refresh

```bash
python pipelines/daily_refresh.py
```

Upserts the most recent raw prices for the tracked instruments.

### 8. Verify the raw load

```bash
python pipelines/test.py
```

Prints a sector-level summary from `raw.market_prices`.

## Analytics available

`compute_indicators.py` populates:

- `daily_return_pct`
- `weekly_return_pct`
- `monthly_return_pct`
- `ma_20`
- `ma_50`
- `ma_200`
- `bb_upper`
- `bb_lower`
- `rsi_14`
- `high_52w`
- `low_52w`
- `pct_from_52w_high`
- `trend_signal`
- `rsi_zone`

`create_views.py` builds:

- `analytics.v_commodities_inr`
- `analytics.v_sector_performance`
- `analytics.v_crude_energy_correlation`
- `analytics.v_portfolio_daily`

## Environment setup

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=india_market
DB_USER=postgres
DB_PASSWORD=your_password
```

Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If you plan to run the Airflow DAG, install Apache Airflow separately in the environment used by your scheduler and workers.
For this project, the Airflow environment should install:

```bash
pip install -r requirements-airflow.txt
```

## Airflow

`airflow_dags/india_market_dag.py` runs:

1. `daily_refresh.py`
2. `compute_indicators.py`
3. `create_views.py`

The DAG supports these optional environment variables:

- `INDIA_MARKET_PROJECT_DIR`
- `INDIA_MARKET_PYTHON_BIN`

The pipeline scripts validate their runtime dependencies with `pipelines/runtime_guard.py`, so the project venv used by Airflow should match `requirements.txt`.

For a cleaner WSL or Ubuntu startup flow, use the helper scripts in `scripts/airflow/`:

```bash
cp scripts/airflow/airflow.env.example scripts/airflow/airflow.env
# edit scripts/airflow/airflow.env once
bash scripts/airflow/start.sh
bash scripts/airflow/status.sh
bash scripts/airflow/stop.sh
```

`start.sh` copies the DAG into `$AIRFLOW_HOME/dags` and starts:

- `scheduler`
- `dag-processor`
- `api-server`

## Current status

- `dbt_projects/`, `notebooks/`, and `data/` are still placeholders
- SQL is externalized under `sql/` and loaded at runtime through `pipelines/sql_loader.py`
- `pipelines/test.py` is a verification script, not a formal automated test suite
