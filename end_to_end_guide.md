# End-to-End Setup and Code Walkthrough

This document explains the project from zero to production-style operation.
It is written as an onboarding guide for someone who wants to understand:

- what the system does
- how to install and run it
- why each step exists
- how the Python and SQL files work together
- how the Airflow orchestration layer fits on top

## 1. What This Project Is

This repository is a small market data platform focused on Indian markets.

At a high level, it does four things:

1. Pulls market data from Yahoo Finance.
2. Stores the raw data in PostgreSQL.
3. Converts that raw data into an analytics-friendly star schema.
4. Computes technical indicators and exposes reporting views.

The system tracks:

- Indian equities across IT, Banking, Pharma, Energy, and FMCG
- commodity futures like Gold, Crude Oil, and Silver
- market indexes like NIFTY and SENSEX
- USD/INR forex data

The main warehouse layers are:

- `raw`: raw market prices as received from Yahoo Finance
- `staging`: currently reserved for future use
- `analytics`: dimensions, fact table, and views

## 2. Big-Picture Architecture

The logical data flow is:

1. `yfinance` downloads OHLCV data.
2. Python loaders insert rows into `raw.market_prices`.
3. Dimension tables are created in `analytics`.
4. Indicator logic reads raw prices and company metadata.
5. A fact table is rebuilt in `analytics.fct_daily_prices`.
6. SQL views provide reporting-ready outputs.
7. Airflow can automate the daily refresh path.

The orchestration flow is:

- first-time bootstrap:
  - `create_everything.py`
  - `setup_and_load.py`
  - `setup_dimensions.py`
  - `fix_dim_dates.py` only for older databases
  - `compute_indicators.py`
  - `create_views.py`
- recurring daily operation:
  - `daily_refresh.py`
  - `compute_indicators.py`
  - `create_views.py`

## 3. Repository Map

Important directories and files:

- `pipelines/`
  - Python entry points for each stage of the ETL flow
- `sql/`
  - SQL used by the Python scripts
- `airflow_dags/india_market_dag.py`
  - Airflow DAG for the recurring daily flow
- `scripts/airflow/`
  - WSL and Ubuntu helper scripts for starting Airflow cleanly
- `.env`
  - database connection settings for the project runtime
- `requirements.txt`
  - Python dependencies for the project runtime
- `requirements-airflow.txt`
  - convenience file for Airflow-related installs

## 4. Environments and Why They Matter

This project works best when you separate the runtime into two Python environments.

### 4.1 Project runtime

This environment runs:

- `create_everything.py`
- `setup_and_load.py`
- `setup_dimensions.py`
- `fix_dim_dates.py`
- `compute_indicators.py`
- `create_views.py`
- `daily_refresh.py`
- `test.py`

Why keep it separate:

- the project pins exact versions in `requirements.txt`
- `pipelines/runtime_guard.py` checks those versions at runtime
- the ETL code had compatibility issues when mixed with a different Airflow environment

### 4.2 Airflow runtime

This environment runs:

- `airflow scheduler`
- `airflow dag-processor`
- `airflow api-server`

Why keep it separate:

- Airflow has its own dependency constraints
- mixing Airflow packages with the project runtime can cause import or SQLAlchemy issues
- the DAG only needs to call the project scripts, not install all ETL dependencies inside the Airflow core environment

## 5. Required Software

You need:

- PostgreSQL
- Python 3
- a project virtual environment
- optionally, WSL or Ubuntu plus a separate Airflow virtual environment

For local orchestration in Windows, the cleanest model is:

- Windows or WSL path for the repo
- PostgreSQL running locally
- Airflow running in WSL or Ubuntu
- project scripts running through a dedicated Python binary referenced by Airflow

## 6. Project Installation and First-Time Setup

This section explains both the commands and the reason for each one.

### 6.1 Create the `.env` file

Create a `.env` file in the project root with:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=india_market
DB_USER=postgres
DB_PASSWORD=your_password
```

Why this exists:

- every pipeline script calls `load_dotenv()`
- the scripts build their SQLAlchemy or psycopg2 connections from these values
- keeping connection settings in `.env` avoids hardcoding them in Python

### 6.2 Create the project virtual environment

Example:

```bash
python -m venv venv
venv\Scripts\activate
# or on Linux / WSL:
# source venv/bin/activate
pip install -r requirements.txt
```

Why this exists:

- the ETL code depends on pinned versions
- `runtime_guard.py` validates that the environment matches those versions
- this keeps local runs and Airflow task runs consistent

### 6.3 Run `create_everything.py`

Command:

```bash
python pipelines/create_everything.py
```

Why this step exists:

- the rest of the pipeline expects the target database and schemas to exist
- it creates the warehouse foundation before any data is loaded

What it does internally:

1. Reads database credentials from `.env`.
2. Connects to the default `postgres` database using `psycopg2`.
3. Checks whether the target database already exists with `sql/create_everything/check_db_exists.sql`.
4. Creates the target database if missing.
5. Connects to the target database using SQLAlchemy.
6. Runs `sql/create_everything/create_schemas_and_table.sql`.
7. Verifies schemas, tables, and the initial row count.

Warehouse objects created here:

- schemas:
  - `raw`
  - `staging`
  - `analytics`
- table:
  - `raw.market_prices`

Why `raw.market_prices` matters:

- it is the landing zone for all downloaded OHLCV data
- it preserves the daily market record at the source grain
- downstream transforms always begin here

### 6.4 Run `setup_and_load.py`

Command:

```bash
python pipelines/setup_and_load.py
```

Why this step exists:

- a warehouse is not useful until raw data is loaded
- this performs the initial historical backfill
- it gives the analytics layer enough history to compute rolling indicators

What it does internally:

1. Runs `validate_runtime()` from `runtime_guard.py`.
2. Calls `create_schema()` as a safety check to ensure the raw table exists.
3. Builds a two-year date range ending at the current UTC time.
4. Iterates through the instrument universe from `market_universe.py`.
5. Calls Yahoo Finance via `yf.Ticker(ticker).history(...)`.
6. Normalizes the returned columns.
7. Adds metadata columns:
   - `ticker`
   - `sector`
   - `loaded_at`
8. Inserts rows into `raw.market_prices` with `sql/setup_and_load/insert_market_price.sql`.
9. Prints a load summary using `sql/setup_and_load/load_summary.sql`.

Important design choices:

- the insert uses `ON CONFLICT DO NOTHING`
- this makes the historical load idempotent for rows that already exist
- throttling with `time.sleep(0.4)` reduces pressure on the data source

Why the market universe is centralized:

- `pipelines/market_universe.py` defines the tracked tickers once
- both historical load and daily refresh use the same source of truth
- this avoids one script loading a different set of assets than another

### 6.5 Run `setup_dimensions.py`

Command:

```bash
python pipelines/setup_dimensions.py
```

Why this step exists:

- raw prices alone are not enough for analytics
- dimensional tables make joins, reporting, and enrichment easier
- the fact table needs foreign keys into those dimensions

What it does internally:

1. Creates `analytics.dim_companies`.
2. Inserts the curated list of tracked instruments into `dim_companies`.
3. Creates `analytics.dim_dates`.
4. Populates `dim_dates` from 2020-01-01 through 2027-12-31.
5. Creates `analytics.fct_daily_prices`.
6. Prints row counts for the dimensions and fact shell.

Why `dim_companies` exists:

- it stores metadata that raw prices do not contain
- examples:
  - company name
  - sector
  - industry
  - market-cap tier
  - membership flags
  - commodity and index flags

Why `dim_dates` exists:

- it converts plain dates into analytics-friendly calendar attributes
- examples:
  - day name
  - month
  - quarter
  - fiscal year
  - fiscal quarter

Why the fact table is created before computation:

- it defines the final analytics schema
- it gives `compute_indicators.py` a safe and known load target
- it enforces grain and uniqueness with `UNIQUE(ticker, date_key)`

### 6.6 Run `fix_dim_dates.py` only when needed

Command:

```bash
python pipelines/fix_dim_dates.py
```

Why this script exists:

- earlier versions of the project had `dim_dates` shape or sizing issues
- this script repairs older databases without requiring a full rebuild

What it does internally:

1. Alters legacy `dim_dates` column sizes if needed.
2. Repopulates `dim_dates`.
3. Ensures the fact table definition still exists.
4. Prints row counts for key tables.

When to use it:

- use it on an older database that was created before the current `dim_dates` definition
- skip it on a fresh database unless you want the extra safety step

### 6.7 Run `compute_indicators.py`

Command:

```bash
python pipelines/compute_indicators.py
```

Why this step exists:

- raw prices are useful for storage
- enriched prices are useful for analytics, screens, and dashboards
- this step converts raw rows into analysis-ready facts

What it does internally:

1. Runs `validate_runtime()`.
2. Loads raw price rows plus `company_key` using `sql/compute_indicators/load_raw_prices.sql`.
3. Converts numeric columns from database values into pandas numeric types.
4. Groups data by ticker.
5. Sorts each ticker's history by date.
6. Computes:
   - daily return
   - weekly return
   - monthly return
   - 20-day moving average
   - 50-day moving average
   - 200-day moving average
   - Bollinger Bands
   - 14-day RSI
   - 52-week high
   - 52-week low
   - percent from 52-week high
   - trend signal
   - RSI zone
7. Derives `date_key` in `YYYYMMDD` integer format.
8. Renames price columns to match the fact schema.
9. Truncates `analytics.fct_daily_prices`.
10. Inserts the rebuilt fact rows in batches.
11. Prints fact-row and summary diagnostics.

Why the script truncates and reloads:

- rolling indicators depend on prior rows
- recomputing the whole fact table avoids drift or partial updates
- this keeps every run consistent with the latest raw history

Why numeric normalization is important:

- PostgreSQL `NUMERIC` values can arrive as decimal types
- pandas rolling math expects numeric arrays it can safely operate on
- the normalization step prevents mixed-type arithmetic failures

### 6.8 Run `create_views.py`

Command:

```bash
python pipelines/create_views.py
```

Why this step exists:

- views turn the fact table into business-facing analytics outputs
- they keep reporting logic in SQL instead of duplicating it in notebooks or dashboards

What it creates:

- `analytics.v_commodities_inr`
- `analytics.v_sector_performance`
- `analytics.v_crude_energy_correlation`
- `analytics.v_portfolio_daily`

Why each view exists:

- `v_commodities_inr`
  - converts commodity prices and returns into INR terms using USD/INR
- `v_sector_performance`
  - summarizes sector-level returns, RSI, and trend counts at the latest date
- `v_crude_energy_correlation`
  - measures how energy stocks correlate with INR-adjusted crude moves
- `v_portfolio_daily`
  - compares a simple equally weighted stock basket with NIFTY

### 6.9 Run `test.py`

Command:

```bash
python pipelines/test.py
```

Why this step exists:

- it is a quick verification script
- it provides a simple sanity check against `raw.market_prices`
- it is not a formal unit test suite

What it prints:

- sector
- distinct ticker count
- raw row count
- date range in the raw table

## 7. Daily Operation After the First Load

Once the historical load and modeling are complete, the day-2 flow is shorter.

### 7.1 Run `daily_refresh.py`

Command:

```bash
python pipelines/daily_refresh.py
```

Why this step exists:

- you do not need to reload two years of history every day
- you only need the newest few market days so the raw table stays current

What it does internally:

1. Runs `validate_runtime()`.
2. Loops through all tracked tickers.
3. Requests only `period="5d"` from Yahoo Finance.
4. Normalizes the results.
5. Upserts rows into `raw.market_prices` with `sql/daily_refresh/upsert_market_price.sql`.

Why it uses upsert instead of insert-ignore:

- the daily refresh may revisit the last few rows repeatedly
- `ON CONFLICT DO UPDATE` keeps the latest values for those dates
- this is safer for near-real-time maintenance than ignoring duplicates

### 7.2 Recompute downstream layers

After the raw table changes, run:

```bash
python pipelines/compute_indicators.py
python pipelines/create_views.py
```

Why this is required:

- the fact table depends on raw prices
- the views depend on the fact table
- the downstream layers must be refreshed after raw data changes

## 8. How the Shared Support Files Work

### 8.1 `pipelines/sql_loader.py`

Purpose:

- keeps SQL logic outside of Python code
- makes SQL easier to edit, review, and reuse

How it works:

- resolves the project root
- resolves the `sql/` directory
- loads a file by relative path

Why this design is useful:

- Python stays focused on orchestration and dataframe work
- SQL stays focused on DDL, DML, and view logic
- the project is easier to maintain than embedding large SQL strings inline

### 8.2 `pipelines/market_universe.py`

Purpose:

- defines the tracked assets in one place

What it exports:

- `UNIVERSE`
- `SECTOR_MAP`
- `ALL_TICKERS`

Why this matters:

- multiple scripts need the same ticker list
- using one central definition avoids drift

### 8.3 `pipelines/runtime_guard.py`

Purpose:

- verifies that the active runtime matches the pinned dependency versions

Why this matters:

- the project previously hit pandas and SQLAlchemy compatibility issues across environments
- the runtime guard makes those mismatches fail fast

How it works:

- reads installed package versions with `importlib.metadata`
- compares them to `REQUIRED_VERSIONS`
- raises a `RuntimeError` if they differ

## 9. How the SQL Layer Is Organized

The `sql/` directory is grouped by pipeline stage.

### 9.1 `sql/create_everything/`

Purpose:

- database existence checks
- initial warehouse schema creation
- verification queries

### 9.2 `sql/setup_and_load/`

Purpose:

- idempotent raw-table creation
- raw row inserts
- load summaries

### 9.3 `sql/setup_dimensions/`

Purpose:

- DDL and seed data for:
  - `dim_companies`
  - `dim_dates`
  - `fct_daily_prices`

### 9.4 `sql/fix_dim_dates/`

Purpose:

- compatibility repair for legacy schemas

### 9.5 `sql/compute_indicators/`

Purpose:

- extract raw rows for indicator computation
- truncate and reload the fact table
- post-load summaries

### 9.6 `sql/create_views/`

Purpose:

- business-facing analytics views

### 9.7 `sql/test/`

Purpose:

- quick raw-layer verification

## 10. Airflow Orchestration

The recurring production-style flow is defined in `airflow_dags/india_market_dag.py`.

Task order:

1. `fetch_latest_prices`
2. `compute_indicators`
3. `create_views`

Why this order is correct:

- raw prices must be refreshed first
- indicators depend on raw prices
- views depend on the indicator-enriched fact table

What the DAG actually does:

- uses `BashOperator`
- changes into the project directory
- runs the target pipeline script with the configured Python binary

Important environment variables:

- `INDIA_MARKET_PROJECT_DIR`
- `INDIA_MARKET_PYTHON_BIN`

Why those variables exist:

- Airflow can live outside the repo
- the DAG still needs a stable path to the project
- the DAG should run the project scripts with the project virtual environment, not the Airflow core environment

Schedule:

- `30 10 * * 1-5`

Meaning:

- 10:30 UTC, Monday through Friday
- that is 16:00 IST

## 11. Clean Airflow Startup on WSL or Ubuntu

The repo includes helper scripts in `scripts/airflow/`.

Files:

- `scripts/airflow/airflow.env.example`
- `scripts/airflow/common.sh`
- `scripts/airflow/start.sh`
- `scripts/airflow/status.sh`
- `scripts/airflow/stop.sh`

### 11.1 Why these scripts exist

- Airflow 3 uses multiple processes:
  - scheduler
  - dag-processor
  - api-server
- starting them by hand with repeated `export` commands is error-prone
- WSL path handling is easier when the startup flow is standardized

### 11.2 How to use them

First copy the template:

```bash
cp scripts/airflow/airflow.env.example scripts/airflow/airflow.env
```

Then edit `scripts/airflow/airflow.env` with your real values.

Then start Airflow:

```bash
bash scripts/airflow/start.sh
```

Check status:

```bash
bash scripts/airflow/status.sh
```

Stop services:

```bash
bash scripts/airflow/stop.sh
```

What `start.sh` does:

1. Loads your local Airflow env file.
2. Verifies required environment variables exist.
3. Verifies the Airflow binary and project Python binary exist.
4. Copies the DAG file into `$AIRFLOW_HOME/dags`.
5. Starts scheduler, dag-processor, and api-server in the background.
6. Writes PID and log files under `$AIRFLOW_HOME/local-run/`.

Why the DAG file is copied instead of symlinked:

- WSL file watching and scheduler refresh behavior can be less reliable across mounted Windows paths
- copying the file makes the Airflow DAG folder unambiguous

## 12. Recommended First-Time Run Order

For a fresh install, run these in order:

```bash
python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py
# optional on a brand-new database, recommended only for older databases:
# python pipelines/fix_dim_dates.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/test.py
```

After that, your recurring cycle is:

```bash
python pipelines/daily_refresh.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
```

If Airflow is enabled, it automates that recurring cycle.

## 13. Common Failure Modes and Why They Happen

### 13.1 Runtime dependency mismatch

Symptom:

- `Runtime dependency mismatch: ...`

Why it happens:

- the active environment does not match `requirements.txt`

Fix:

- install the pinned versions in the project venv
- make Airflow tasks use the project venv through `INDIA_MARKET_PYTHON_BIN`

### 13.2 Airflow login issues

Symptom:

- `401 Unauthorized`
- invalid credentials

Why it happens:

- Airflow Simple Auth is enabled, but the user or generated password was not set up correctly

Fix:

- set `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS`
- restart Airflow
- read the generated password file

### 13.3 Airflow DAG not appearing

Symptom:

- DAG file exists but the UI does not show it

Why it happens:

- the DAG was not copied into the real Airflow DAG folder
- the scheduler or dag-processor is not running
- a parse issue prevented serialization

Fix:

- use `scripts/airflow/start.sh`
- confirm `dag-processor` is running
- use `airflow dags list-import-errors`

### 13.4 Raw rows exist but fact table is empty

Symptom:

- `raw.market_prices` has data
- `analytics.fct_daily_prices` has no rows

Why it happens:

- `compute_indicators.py` has not run successfully
- `dim_companies` or `dim_dates` was never created

Fix:

- run `setup_dimensions.py`
- then run `compute_indicators.py`

## 14. Mental Model for the Whole System

If you want one simple way to think about the repo, it is this:

- `create_everything.py` creates the warehouse shell
- `setup_and_load.py` fills the raw layer
- `setup_dimensions.py` creates analytics dimensions
- `fix_dim_dates.py` repairs older schemas
- `compute_indicators.py` creates the analytics fact table
- `create_views.py` creates business-facing reporting outputs
- `daily_refresh.py` keeps raw data current
- `test.py` gives a quick verification view
- `india_market_dag.py` automates the recurring part

That is the end-to-end lifecycle of the project.
