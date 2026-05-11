# Indian Market Intelligence Pipeline

An end-to-end Python, PostgreSQL, and Airflow project for Indian market analytics. The pipeline collects OHLCV data from Yahoo Finance, stores it in a raw schema, builds analytics dimensions and fact tables, computes technical indicators, publishes reporting views, and generates AI-assisted market commentary for dashboard use.

The core project is complete: historical loading, daily refresh, technical indicator generation, analytics views, Airflow orchestration, and Gemini-powered commentary are implemented in the repository.

## What This Project Delivers

- Tracks 59 instruments across Indian equities, indices, commodities, and USD/INR.
- Loads market prices into PostgreSQL from Yahoo Finance.
- Models data into `raw`, `staging`, and `analytics` schemas.
- Builds company and date dimensions plus an enriched daily price fact table.
- Computes returns, moving averages, Bollinger Bands, RSI, 52-week range metrics, and trend labels.
- Creates reusable analytics views for sectors, commodities, portfolio-style summaries, gold returns, and crude-energy correlation.
- Runs daily refreshes through an Airflow DAG after market close.
- Generates short AI market commentary and stores it in `analytics.ai_commentary`.

## Tech Stack

- Python 3
- PostgreSQL
- SQLAlchemy
- psycopg2
- pandas
- yfinance
- python-dotenv
- Google Gemini API via `google-generativeai`
- Apache Airflow for orchestration

## Project Structure

```text
MKT-1/
|-- airflow_dags/
|   `-- india_market_dag.py
|-- data/
|-- dbt_projects/
|-- notebooks/
|-- pipelines/
|   |-- ai_commentary.py
|   |-- compute_indicators.py
|   |-- create_everything.py
|   |-- create_sector_correlation.py
|   |-- create_views.py
|   |-- daily_refresh.py
|   |-- fix_correlation_views.py
|   |-- fix_dim_dates.py
|   |-- market_universe.py
|   |-- runtime_guard.py
|   |-- setup_and_load.py
|   |-- setup_dimensions.py
|   |-- sql_loader.py
|   `-- test.py
|-- scripts/
|   `-- airflow/
|       |-- airflow.env.example
|       |-- common.sh
|       |-- start.sh
|       |-- status.sh
|       `-- stop.sh
|-- sql/
|   |-- compute_indicators/
|   |-- create_everything/
|   |-- create_views/
|   |-- daily_refresh/
|   |-- fix_dim_dates/
|   |-- setup_and_load/
|   |-- setup_dimensions/
|   `-- test/
|-- .env
|-- .gitignore
|-- README.md
|-- requirements-airflow.txt
`-- requirements.txt
```

## Market Universe

The universe is defined in `pipelines/market_universe.py`.

- IT: TCS, Infosys, Wipro, HCLTech, Tech Mahindra, LTIMindtree, and others
- Banking: HDFC Bank, ICICI Bank, SBI, Axis Bank, Kotak Bank, and others
- Pharma: Sun Pharma, Dr. Reddy's, Cipla, Divi's Labs, Apollo Hospitals, and others
- Energy: Reliance, ONGC, NTPC, Power Grid, IOC, and others
- FMCG: Hindustan Unilever, ITC, Nestle India, Britannia, Dabur, and others
- Commodities: gold, crude oil, and silver futures
- Indices and macro: NIFTY 50, Sensex, Bank NIFTY, NIFTY IT, India VIX, and USD/INR

## Data Model

### Raw Schema

- `raw.market_prices`: daily OHLCV market prices keyed by ticker and date.

### Analytics Schema

- `analytics.dim_companies`: instrument metadata, sector mapping, and stock/index/commodity flags.
- `analytics.dim_dates`: calendar and fiscal date attributes.
- `analytics.fct_daily_prices`: enriched daily price fact table with returns and technical indicators.
- `analytics.ai_commentary`: generated market commentary snapshots.

## Analytics Views

`pipelines/create_views.py` builds:

- `analytics.v_commodities_inr`
- `analytics.v_gold_monthly_returns`
- `analytics.v_sector_performance`
- `analytics.v_crude_energy_correlation`
- `analytics.v_portfolio_daily`

`pipelines/create_sector_correlation.py` also creates:

- `analytics.v_sector_correlation`

## Indicators

`pipelines/compute_indicators.py` populates:

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

## Environment Setup

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=india_market
DB_USER=postgres
DB_PASSWORD=your_postgres_password

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT_SECONDS=30
```

`GEMINI_API_KEY` is required only for `pipelines/ai_commentary.py` and the final Airflow commentary task.

Install the project dependencies in Windows PowerShell:

```powershell
cd D:\DataAnalyst\MKT-1
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run The Pipeline Manually

Run these commands from Windows PowerShell in the project root:

```powershell
cd D:\DataAnalyst\MKT-1
venv\Scripts\activate

python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/create_sector_correlation.py
python pipelines/ai_commentary.py
python pipelines/test.py
```

For an existing database that was created before the current date dimension shape, run this once before recomputing indicators:

```powershell
python pipelines/fix_dim_dates.py
```

If old indicator rows contain `NaN` values that affect correlation output, run:

```powershell
python pipelines/fix_correlation_views.py
```

## Daily Refresh Flow

After the initial historical load, use:

```powershell
python pipelines/daily_refresh.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/ai_commentary.py
```

`daily_refresh.py` upserts the latest market prices, then the remaining scripts rebuild derived analytics and commentary.

## Airflow Orchestration

The DAG is defined in `airflow_dags/india_market_dag.py`.

It runs:

1. `daily_refresh.py`
2. `compute_indicators.py`
3. `create_views.py`
4. `ai_commentary.py`

The DAG ID is `india_market_daily`, scheduled at `30 10 * * 1-5`, with retries and a two-hour task timeout.

For the WSL or Ubuntu Airflow helper workflow:

```bash
cd /mnt/d/DataAnalyst/MKT-1
cp scripts/airflow/airflow.env.example scripts/airflow/airflow.env
# edit scripts/airflow/airflow.env once
bash scripts/airflow/start.sh
bash scripts/airflow/status.sh
bash scripts/airflow/stop.sh
```

The helper script copies the DAG into `$AIRFLOW_HOME/dags` and starts the scheduler, DAG processor, and API server.

## Verification

Use the lightweight verification script:

```powershell
python pipelines/test.py
```

It prints a sector-level summary from `raw.market_prices`. The repository currently uses this as a smoke test rather than a formal automated test suite.

## Current Status

- Complete: ingestion, schema setup, dimensional modeling, indicators, analytics views, daily refresh, Airflow orchestration, and AI commentary.
- Ready for dashboard integration through the `analytics` views and `analytics.ai_commentary`.
- Placeholders remain for future expansion in `dbt_projects/`, `notebooks/`, and `data/`.
- Extra local project notes are intentionally ignored by Git; `README.md` is the primary tracked documentation file.
