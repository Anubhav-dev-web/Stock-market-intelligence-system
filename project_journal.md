# Project Journal

Date: 2026-03-17

This file is a compact handoff note based on the implementation and troubleshooting work completed in this repo.
It is meant to preserve the most useful parts of the working session in a form that lives with the codebase.

For the full architecture and setup walkthrough, see `end_to_end_guide.md`.

## 1. Current State

The project is now in a workable state with:

- a sequential ETL flow for first-time setup
- a recurring daily refresh flow
- a working Airflow DAG for the daily pipeline
- WSL and Ubuntu helper scripts for cleaner Airflow startup
- a runtime guard to prevent dependency drift in the project environment

The main recurring DAG is:

- `fetch_latest_prices`
- `compute_indicators`
- `create_views`

The Airflow schedule is:

- `30 10 * * 1-5`
- this is 10:30 UTC, or 16:00 IST, Monday to Friday

## 2. Major Changes Made

### 2.1 Pipeline and schema fixes

The project was aligned so the code, SQL files, and docs match each other more closely.

Key fixes:

- `pipelines/compute_indicators.py`
  - now loads SQL from `sql/compute_indicators/`
  - truncates `analytics.fct_daily_prices` before reload
  - includes `adj_close`
  - avoids pandas SQL helper compatibility problems by using SQLAlchemy execution directly
  - normalizes numeric types to prevent `Decimal` vs `float` errors
- `pipelines/create_views.py`
  - now uses external SQL files under `sql/create_views/`
- `pipelines/daily_refresh.py`
  - uses upsert logic from `sql/daily_refresh/upsert_market_price.sql`
  - shares the same ticker universe as the historical load
- `pipelines/setup_and_load.py`
  - uses the shared market universe
  - uses timezone-aware UTC timestamps
- `pipelines/setup_dimensions.py`
  - creates and populates dimensions and the fact table shell consistently
- `pipelines/fix_dim_dates.py`
  - repairs older databases so legacy `dim_dates` setups can still work
- `airflow_dags/india_market_dag.py`
  - now uses environment variables for project path and Python binary
  - keeps the DAG limited to the three real runtime tasks

### 2.2 New support files

Added:

- `pipelines/market_universe.py`
  - single source of truth for tracked instruments
- `pipelines/runtime_guard.py`
  - validates the project runtime package versions
- `requirements.txt`
  - project runtime dependencies
- `requirements-airflow.txt`
  - Airflow-side install helper
- `scripts/airflow/`
  - helper scripts for WSL and Ubuntu Airflow startup
- `end_to_end_guide.md`
  - complete system walkthrough

## 3. Airflow and WSL Decisions

The main operational lesson from the setup work was:

- do not mix the Airflow core environment and the project runtime environment

Recommended layout:

- Airflow venv:
  - `~/airflow_venv`
- project venv:
  - `~/india_market_venv`
- Airflow home:
  - `~/airflow`

Why this matters:

- the project had pandas and SQLAlchemy compatibility issues when run under a mismatched Airflow environment
- Airflow itself also has its own dependency constraints
- keeping the two environments separate is the cleanest model

Key environment variables:

- `AIRFLOW_HOME`
- `INDIA_MARKET_PROJECT_DIR`
- `INDIA_MARKET_PYTHON_BIN`
- `AIRFLOW__API_AUTH__JWT_SECRET`
- `AIRFLOW__API__SECRET_KEY`
- `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS`

## 4. Important Troubleshooting Outcomes

These were the major runtime issues encountered and the fixes that resolved them.

### 4.1 Airflow task worked locally but failed in Linux

Root cause:

- the local Windows environment and the Airflow Linux environment were not the same
- pandas and SQLAlchemy behavior differed between environments

Fix:

- separate the Airflow venv from the project venv
- make the DAG run project scripts with `INDIA_MARKET_PYTHON_BIN`
- remove pandas SQL helper dependence from `compute_indicators.py`

### 4.2 `Engine` / `cursor` and `read_sql` errors

Root cause:

- pandas SQL helpers were not reliable with the Airflow environment's package combination

Fix:

- `compute_indicators.py` now uses SQLAlchemy result rows directly
- the fact load now uses explicit batch insert SQL

### 4.3 `decimal.Decimal` vs `float` math failure

Root cause:

- PostgreSQL numeric values were arriving in a form that mixed poorly with pandas math

Fix:

- normalize numeric columns immediately after loading the raw data into pandas

### 4.4 Running `.py` directly in Linux shell

Symptom:

- `import: command not found`
- `$'\r': command not found`

Root cause:

- the file was being executed as a shell script instead of via Python

Fix:

- run scripts like:
  - `/home/maximus/airflow_venv/bin/python3 pipelines/compute_indicators.py`

### 4.5 Airflow login failed with `401 Unauthorized`

Root cause:

- Airflow was using `SimpleAuthManager`
- the generated password flow had not been followed correctly

Fix:

- set `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS`
- restart Airflow
- use the generated password file for login

## 5. What Was Verified

During the working session, the following outcomes were confirmed:

- the pipeline scripts compile cleanly
- the project runtime works end to end locally
- the Airflow UI came up successfully on port 8080
- the `india_market_daily` DAG appeared in the Airflow UI
- a triggered DAG run completed with all three tasks green:
  - `fetch_latest_prices`
  - `compute_indicators`
  - `create_views`

## 6. How to Operate the Project Now

### 6.1 First-time build

Run in this order:

```bash
python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/test.py
```

Optional for older databases:

```bash
python pipelines/fix_dim_dates.py
```

### 6.2 Daily manual refresh

Run:

```bash
python pipelines/daily_refresh.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
```

### 6.3 Airflow startup in WSL or Ubuntu

Use:

```bash
cp scripts/airflow/airflow.env.example scripts/airflow/airflow.env
# edit the file once
bash scripts/airflow/start.sh
bash scripts/airflow/status.sh
```

To stop services:

```bash
bash scripts/airflow/stop.sh
```

## 7. Known Operating Assumptions

- the PostgreSQL database is reachable using the values in `.env`
- the project venv matches `requirements.txt`
- Airflow is started with its own environment, not the project environment
- the DAG file is copied into the actual Airflow DAG directory by the helper scripts
- `scripts/airflow/airflow.env` should remain local and is ignored by git

## 8. Good Next Improvements

If you continue developing this repo, the highest-value next steps are:

- add formal automated tests instead of relying on `pipelines/test.py`
- add a small health-check or smoke-test script for Airflow task validation
- consider adding a staging layer if transformations become more complex
- document the expected PostgreSQL setup more explicitly
- add notebook or dashboard examples that consume the analytics views

## 9. Short Mental Model

If you need the quickest possible summary:

- `create_everything.py` builds the warehouse shell
- `setup_and_load.py` backfills the raw table
- `setup_dimensions.py` creates dimensions and the fact shell
- `compute_indicators.py` rebuilds the analytics fact table
- `create_views.py` builds reporting views
- `daily_refresh.py` keeps the raw table current
- `india_market_dag.py` automates the daily refresh path

That is the current working shape of the system.
