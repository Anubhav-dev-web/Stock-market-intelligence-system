# Walkthrough: SQL Extraction from Pipeline Files

## What Changed

Extracted **all embedded SQL strings** from 6 Python pipeline files into **25 standalone [.sql](file:///d:/DataAnalyst/MKT-1/sql/test/sector_summary.sql) files** under [sql/](file:///d:/DataAnalyst/MKT-1/sql/test/sector_summary.sql), organized by pipeline sub-folder. A new [sql_loader.py](file:///d:/DataAnalyst/MKT-1/pipelines/sql_loader.py) utility loads SQL at runtime.

### New File Tree

```
sql/
├── create_everything/
│   ├── check_db_exists.sql
│   ├── create_schemas_and_table.sql
│   ├── verify_schemas.sql
│   ├── verify_tables.sql
│   └── count_market_prices.sql
├── setup_and_load/
│   ├── create_schema.sql
│   ├── check_table_exists.sql
│   ├── insert_market_price.sql
│   └── load_summary.sql
├── setup_dimensions/
│   ├── create_dim_companies.sql
│   ├── insert_dim_companies.sql
│   ├── create_dim_dates.sql
│   ├── insert_dim_dates.sql
│   ├── create_fct_daily_prices.sql
│   └── verify_tables.sql
├── fix_dim_dates/
│   ├── alter_column_sizes.sql
│   ├── insert_dim_dates.sql
│   ├── create_fct_daily_prices.sql
│   └── verify_tables.sql
├── compute_indicators/
│   ├── load_raw_prices.sql
│   ├── truncate_fct.sql
│   ├── trend_summary.sql
│   ├── rsi_summary.sql
│   └── count_fct.sql
└── test/
    └── sector_summary.sql

pipelines/
├── sql_loader.py          ← NEW helper
├── create_everything.py   ← refactored
├── setup_and_load.py      ← refactored
├── setup_dimensions.py    ← refactored
├── fix_dim_dates.py       ← refactored
├── compute_indecators.py  ← refactored
└── test.py                ← refactored
```

## How It Works

Each pipeline imports [load_sql()](file:///d:/DataAnalyst/MKT-1/pipelines/sql_loader.py#10-23) which reads [.sql](file:///d:/DataAnalyst/MKT-1/sql/test/sector_summary.sql) files relative to the project's [sql/](file:///d:/DataAnalyst/MKT-1/sql/test/sector_summary.sql) directory:

```python
from sql_loader import load_sql
# ...
conn.execute(text(load_sql('setup_and_load/create_schema.sql')))
```

## Verification

| Check | Result |
|-------|--------|
| `py_compile` on all 7 Python files | ✅ All compile OK |
| [load_sql()](file:///d:/DataAnalyst/MKT-1/pipelines/sql_loader.py#10-23) smoke test | ✅ Reads SQL content correctly |

## How to Run (unchanged)

```bash
python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py   # or fix_dim_dates.py
python pipelines/compute_indecators.py
python pipelines/test.py
```
