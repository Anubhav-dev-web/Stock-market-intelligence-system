# 📈 Stock Market Intelligence System

A **Python + PostgreSQL ETL pipeline** that ingests 2 years of Indian stock market data from Yahoo Finance, builds a dimensional data model (star schema), and computes technical indicators for 59 instruments across 7 sectors.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Pipeline Steps](#pipeline-steps)
- [Stock Universe](#stock-universe)
- [Technical Indicators](#technical-indicators)
- [Getting Started](#getting-started)
- [SQL File Reference](#sql-file-reference)

---

## Architecture Overview

```
Yahoo Finance API ──► ETL Pipeline (Python) ──► PostgreSQL Database
                           │
      ┌────────────────────┼──────────────────────┐
      │                    │                      │
 1. create_everything  2. setup_and_load   3. setup_dimensions
   (DB + schemas)      (raw ingestion)      (dim tables)
                                                  │
                                           4. fix_dim_dates
                                             (schema fixes)
                                                  │
                                           5. compute_indicators
                                             (fact table + analytics)
```

**Data flow:**
1. **Extract** — Pull OHLCV data from Yahoo Finance via `yfinance`
2. **Load** — Insert into `raw.market_prices` with conflict handling
3. **Transform** — Compute technical indicators (RSI, MAs, Bollinger Bands, etc.)
4. **Store** — Load enriched data into `analytics.fct_daily_prices` star schema

---

## Tech Stack

| Component   | Technology                          |
|-------------|-------------------------------------|
| Language    | Python 3.x                          |
| Database    | PostgreSQL                          |
| Data Source | Yahoo Finance (`yfinance`)          |
| ORM / SQL   | SQLAlchemy + raw SQL files          |
| Data Wrangling | pandas                           |
| Config      | `python-dotenv` (`.env` file)       |
| DB Driver   | `psycopg2`                          |

---

## Project Structure

```
MKT-1/
├── .env                          # Database credentials (gitignored)
├── .gitignore
├── README.md
│
├── pipelines/                    # Python ETL scripts
│   ├── sql_loader.py             # Utility: loads SQL files from sql/ dir
│   ├── create_everything.py      # Step 1: Create DB, schemas, raw table
│   ├── setup_and_load.py         # Step 2: Ingest data from Yahoo Finance
│   ├── setup_dimensions.py       # Step 3: Create dimension tables
│   ├── fix_dim_dates.py          # Step 3b: Fix dim_dates column sizes
│   ├── compute_indecators.py     # Step 4: Compute indicators → fact table
│   └── test.py                   # Verification: sector summary query
│
├── sql/                          # All SQL separated by pipeline module
│   ├── create_everything/        # 5 SQL files
│   ├── setup_and_load/           # 4 SQL files
│   ├── setup_dimensions/         # 6 SQL files
│   ├── fix_dim_dates/            # 4 SQL files
│   ├── compute_indicators/       # 5 SQL files
│   └── test/                     # 1 SQL file
│
├── airflow_dags/                 # (Planned) Airflow DAGs
├── dbt_projects/                 # (Planned) dbt transformations
├── notebooks/                    # (Planned) Jupyter analysis notebooks
├── data/                         # (Planned) CSV exports
└── venv/                         # Python virtual environment (gitignored)
```

---

## Database Schema

**Database:** `india_market`  
**Schemas:** `raw` → `staging` → `analytics`

### Star Schema Diagram

```
                   ┌──────────────────────┐
                   │  analytics.dim_dates  │
                   ├──────────────────────┤
                   │ date_key (PK)         │
                   │ full_date             │
                   │ day_of_week           │
                   │ day_name              │
                   │ week_number           │
                   │ month_name / number   │
                   │ quarter               │
                   │ year                  │
                   │ is_weekend            │
                   │ fy_year / fy_quarter  │
                   └─────────┬────────────┘
                             │
┌─────────────────────┐      │      ┌────────────────────────────┐
│ analytics.           │      │      │ analytics.fct_daily_prices  │
│ dim_companies        │      │      ├────────────────────────────┤
├─────────────────────┤      │      │ price_key (PK)              │
│ company_key (PK)     │◄─────┼─────│ company_key (FK)            │
│ ticker (UNIQUE)      │      └─────│ date_key (FK)               │
│ company_name         │            │ ticker                      │
│ sector               │            │ open/high/low/close_price   │
│ industry             │            │ adj_close, volume           │
│ market_cap_tier      │            │ daily/weekly/monthly return  │
│ nifty50_member       │            │ ma_20, ma_50, ma_200        │
│ sensex_member        │            │ bb_upper, bb_lower          │
│ is_commodity         │            │ rsi_14                      │
│ is_index             │            │ high_52w, low_52w           │
│ currency, exchange   │            │ pct_from_52w_high           │
└─────────────────────┘            │ trend_signal, rsi_zone      │
                                    └────────────────────────────┘
```

### Raw Layer

| Table | Description |
|-------|-------------|
| `raw.market_prices` | Raw OHLCV data ingested from Yahoo Finance. Unique constraint on `(ticker, date)`. |

### Analytics Layer

| Table | Type | Description |
|-------|------|-------------|
| `analytics.dim_companies` | Dimension | 59 instruments with metadata (sector, industry, market cap tier, index membership). |
| `analytics.dim_dates` | Dimension | Calendar from 2020–2027 with fiscal year (Indian FY Apr–Mar) and weekend flags. |
| `analytics.fct_daily_prices` | Fact | Enriched daily prices with all computed technical indicators. FK references to both dimensions. |

---

## Pipeline Steps

Run these scripts **sequentially** from the `pipelines/` directory:

### Step 1 — Create Database & Schemas
```bash
python pipelines/create_everything.py
```
- Connects to default `postgres` database
- Creates `india_market` database (if not exists)
- Creates schemas: `raw`, `staging`, `analytics`
- Creates `raw.market_prices` table with indexes

### Step 2 — Ingest Market Data
```bash
python pipelines/setup_and_load.py
```
- Fetches **2 years** of historical OHLCV data from Yahoo Finance
- Loads data for all 59 tickers, one by one with 0.4s throttle
- Inserts into `raw.market_prices` with `ON CONFLICT DO NOTHING`
- Prints a sector-by-sector summary at the end

### Step 3 — Set Up Dimension Tables
```bash
python pipelines/setup_dimensions.py
python pipelines/fix_dim_dates.py       # fixes column size issues
```
- Creates `analytics.dim_companies` with all 59 instruments pre-populated
- Creates `analytics.dim_dates` calendar (2020-01-01 to 2027-12-31)
- Creates empty `analytics.fct_daily_prices` table
- `fix_dim_dates.py` corrects column sizes and re-populates date data

### Step 4 — Compute Technical Indicators
```bash
python pipelines/compute_indecators.py
```
- Reads all raw prices joined with `dim_companies`
- Computes 15+ technical indicators per ticker (see below)
- Truncates and reloads `analytics.fct_daily_prices`
- Prints trend and RSI zone summaries

### Verify
```bash
python pipelines/test.py
```
- Queries sector-level summary from `raw.market_prices`

---

## Stock Universe

**59 instruments** across **7 categories:**

| Sector | Count | Examples |
|--------|-------|---------|
| **IT** | 10 | TCS, Infosys, Wipro, HCL Tech, Tech Mahindra |
| **Banking** | 10 | HDFC Bank, ICICI Bank, SBI, Bajaj Finance, Kotak |
| **Pharma** | 10 | Sun Pharma, Dr. Reddy's, Cipla, Apollo Hospitals |
| **Energy** | 10 | Reliance, ONGC, NTPC, Tata Power, Adani Green |
| **FMCG** | 10 | HUL, ITC, Nestle India, Britannia, Dabur |
| **Commodity** | 3 | Gold Futures, Crude Oil WTI, Silver Futures |
| **Index/Forex** | 6 | NIFTY 50, SENSEX, Bank Nifty, India VIX, USD/INR |

---

## Technical Indicators

Computed in `compute_indecators.py` for each ticker:

| Indicator | Formula / Window | Description |
|-----------|-----------------|-------------|
| `daily_return_pct` | 1-day % change | Daily return |
| `weekly_return_pct` | 5-day % change | Weekly return |
| `monthly_return_pct` | 21-day % change | Monthly return |
| `ma_20` | 20-day SMA | Short-term moving average |
| `ma_50` | 50-day SMA | Medium-term moving average |
| `ma_200` | 200-day SMA | Long-term moving average |
| `bb_upper` / `bb_lower` | 20-day MA ± 2σ | Bollinger Bands |
| `rsi_14` | 14-day RSI | Relative Strength Index |
| `high_52w` / `low_52w` | 252-day rolling max/min | 52-week range |
| `pct_from_52w_high` | `(close - high_52w) / high_52w × 100` | Distance from 52w high |
| `trend_signal` | MA crossover logic | `Strong Bullish` / `Bullish` / `Neutral` / `Bearish` / `Strong Bearish` |
| `rsi_zone` | RSI thresholds | `Overbought` (≥70) / `Oversold` (≤30) / `Neutral` |

---

## Getting Started

### Prerequisites

- **Python 3.8+**
- **PostgreSQL** running on `localhost:5432`

### 1. Clone & Set Up Environment

```bash
git clone <repo-url>
cd MKT-1

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install psycopg2-binary sqlalchemy pandas yfinance python-dotenv
```

### 2. Configure Database Credentials

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=india_market
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. Run the Pipeline

```bash
cd pipelines

# Step 1: Create database, schemas, and raw table
python create_everything.py

# Step 2: Ingest 2 years of market data from Yahoo Finance
python setup_and_load.py

# Step 3: Create dimension tables (companies + dates)
python setup_dimensions.py
python fix_dim_dates.py

# Step 4: Compute technical indicators → fact table
python compute_indecators.py

# Verify: Check sector summary
python test.py
```

---

## SQL File Reference

All SQL is externalized in the `sql/` directory, loaded at runtime via `sql_loader.py`.

<details>
<summary><strong>sql/create_everything/</strong> — Database bootstrapping</summary>

| File | Purpose |
|------|---------|
| `check_db_exists.sql` | Check if `india_market` database exists |
| `create_schemas_and_table.sql` | Create `raw`, `staging`, `analytics` schemas + `raw.market_prices` |
| `verify_schemas.sql` | List all schemas |
| `verify_tables.sql` | List all tables |
| `count_market_prices.sql` | Count rows in `raw.market_prices` |

</details>

<details>
<summary><strong>sql/setup_and_load/</strong> — Data ingestion</summary>

| File | Purpose |
|------|---------|
| `create_schema.sql` | Create schemas + `raw.market_prices` (idempotent) |
| `check_table_exists.sql` | Verify table exists |
| `insert_market_price.sql` | Parameterized INSERT with `ON CONFLICT DO NOTHING` |
| `load_summary.sql` | Sector-level summary aggregation |

</details>

<details>
<summary><strong>sql/setup_dimensions/</strong> — Dimension & fact tables</summary>

| File | Purpose |
|------|---------|
| `create_dim_companies.sql` | Create `analytics.dim_companies` |
| `insert_dim_companies.sql` | Insert all 59 instruments |
| `create_dim_dates.sql` | Create `analytics.dim_dates` |
| `insert_dim_dates.sql` | Generate calendar 2020–2027 with FY logic |
| `create_fct_daily_prices.sql` | Create `analytics.fct_daily_prices` with FK refs |
| `verify_tables.sql` | List all tables across schemas |

</details>

<details>
<summary><strong>sql/fix_dim_dates/</strong> — Schema corrections</summary>

| File | Purpose |
|------|---------|
| `alter_column_sizes.sql` | Fix column size constraints on `dim_dates` |
| `insert_dim_dates.sql` | Re-populate `dim_dates` |
| `create_fct_daily_prices.sql` | Re-create fact table |
| `verify_tables.sql` | Verification queries |

</details>

<details>
<summary><strong>sql/compute_indicators/</strong> — Analytics computation</summary>

| File | Purpose |
|------|---------|
| `load_raw_prices.sql` | JOIN `raw.market_prices` with `dim_companies` |
| `truncate_fct.sql` | Clear `fct_daily_prices` before reload |
| `count_fct.sql` | Count rows in fact table |
| `trend_summary.sql` | Aggregate by `trend_signal` |
| `rsi_summary.sql` | Aggregate by `rsi_zone` |

</details>

<details>
<summary><strong>sql/test/</strong> — Verification</summary>

| File | Purpose |
|------|---------|
| `sector_summary.sql` | Sector-level row counts and date ranges |

</details>

---

## Future Work

| Directory | Planned Purpose |
|-----------|-----------------|
| `airflow_dags/` | Orchestrate daily pipeline runs with Apache Airflow |
| `dbt_projects/` | dbt models for staging and analytics transformations |
| `notebooks/` | Jupyter notebooks for EDA and visualization |
| `data/` | CSV exports for offline analysis |

---

## License

This project is for educational and research purposes.
