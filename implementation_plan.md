# Extract Embedded SQL from Pipeline Files into `sql/` Folder

All 6 Python files in `pipelines/` contain inline SQL strings (DDL, DML, queries). This refactoring extracts every SQL string into standalone `.sql` files under `sql/`, organized by pipeline, and updates the Python files to load SQL from disk at runtime.

## Proposed Changes

### Helper Utility

#### [NEW] [sql_loader.py](file:///d:/DataAnalyst/MKT-1/pipelines/sql_loader.py)
A small utility function `load_sql(filename)` that reads a `.sql` file from the `sql/` folder (path resolved relative to the project root). All pipeline files will use this instead of inline SQL strings.

---

### SQL Files (all new)

Organized into sub-folders matching the pipeline that uses them.

#### `sql/create_everything/`
| File | Contents |
|------|----------|
| [NEW] `check_db_exists.sql` | `SELECT 1 FROM pg_database WHERE datname = 'india_market'` |
| [NEW] `create_schemas_and_table.sql` | CREATE SCHEMA + CREATE TABLE + CREATE INDEX from [create_everything.py](file:///d:/DataAnalyst/MKT-1/pipelines/create_everything.py) lines 54-78 |
| [NEW] `verify_schemas.sql` | Verification query for schemas |
| [NEW] `verify_tables.sql` | Verification query for tables in raw schema |
| [NEW] `count_market_prices.sql` | `SELECT COUNT(*) FROM raw.market_prices` |

#### `sql/setup_and_load/`
| File | Contents |
|------|----------|
| [NEW] `create_schema.sql` | CREATE SCHEMA + CREATE TABLE from lines 22-40 |
| [NEW] `check_table_exists.sql` | `information_schema` check query |
| [NEW] `insert_market_price.sql` | The parameterised INSERT...ON CONFLICT statement |
| [NEW] `load_summary.sql` | The sector summary SELECT |

#### `sql/setup_dimensions/`
| File | Contents |
|------|----------|
| [NEW] `create_dim_companies.sql` | DDL for dim_companies |
| [NEW] `insert_dim_companies.sql` | INSERT with all 59 instrument rows |
| [NEW] `create_dim_dates.sql` | DDL for dim_dates |
| [NEW] `insert_dim_dates.sql` | INSERT...GENERATE_SERIES for dim_dates |
| [NEW] `create_fct_daily_prices.sql` | DDL + indexes for fct_daily_prices |
| [NEW] `verify_tables.sql` | information_schema query |

#### `sql/fix_dim_dates/`
| File | Contents |
|------|----------|
| [NEW] `alter_column_sizes.sql` | ALTER TABLE for day_name, month_name, etc. |
| [NEW] `insert_dim_dates.sql` | Populate dim_dates with TRIM'd values |
| [NEW] `create_fct_daily_prices.sql` | DDL + indexes |
| [NEW] `verify_tables.sql` | information_schema query |

#### `sql/compute_indicators/`
| File | Contents |
|------|----------|
| [NEW] `load_raw_prices.sql` | The JOIN query to read raw data |
| [NEW] `truncate_fct.sql` | TRUNCATE statement |
| [NEW] `trend_summary.sql` | GROUP BY trend_signal query |
| [NEW] `rsi_summary.sql` | GROUP BY rsi_zone query |

#### `sql/test/`
| File | Contents |
|------|----------|
| [NEW] `sector_summary.sql` | The sector summary verification query |

---

### Modified Pipeline Files

#### [MODIFY] [create_everything.py](file:///d:/DataAnalyst/MKT-1/pipelines/create_everything.py)
Replace all inline SQL strings with `load_sql('create_everything/...')` calls.

#### [MODIFY] [setup_and_load.py](file:///d:/DataAnalyst/MKT-1/pipelines/setup_and_load.py)
Replace inline SQL with `load_sql('setup_and_load/...')` calls.

#### [MODIFY] [setup_dimensions.py](file:///d:/DataAnalyst/MKT-1/pipelines/setup_dimensions.py)
Replace inline SQL with `load_sql('setup_dimensions/...')` calls.

#### [MODIFY] [fix_dim_dates.py](file:///d:/DataAnalyst/MKT-1/pipelines/fix_dim_dates.py)
Replace inline SQL with `load_sql('fix_dim_dates/...')` calls.

#### [MODIFY] [compute_indecators.py](file:///d:/DataAnalyst/MKT-1/pipelines/compute_indecators.py)
Replace inline SQL with `load_sql('compute_indicators/...')` calls.

#### [MODIFY] [test.py](file:///d:/DataAnalyst/MKT-1/pipelines/test.py)
Replace inline SQL with `load_sql('test/...')` call.

---

## Key Design Decisions

- **`load_sql()` helper** locates the project root via the relative path `../sql/` from the `pipelines/` directory. This keeps all pipeline files working with `python pipelines/file.py` from the project root **or** `python file.py` from inside `pipelines/`.
- **Sub-folders** inside `sql/` mirror the pipeline that uses each query, making it easy to find which SQL belongs where.
- **No behavioral change** — the Python logic (loops, pandas transforms, logging, etc.) stays identical. Only the source of the SQL text changes.

## Verification Plan

### Automated Tests
- Run `python -c "from pipelines.sql_loader import load_sql; print(load_sql('test/sector_summary.sql')[:50])"` from `d:\DataAnalyst\MKT-1` to confirm the loader works.
- Run `python -c "import py_compile; py_compile.compile('pipelines/create_everything.py', doraise=True)"` (and similarly for each pipeline file) to confirm no syntax errors.

### Manual Verification
- Since the pipelines talk to a live PostgreSQL database, the user should run each pipeline as before:
  1. `python pipelines/create_everything.py`
  2. `python pipelines/setup_and_load.py`
  3. `python pipelines/setup_dimensions.py` or `python pipelines/fix_dim_dates.py`
  4. `python pipelines/compute_indecators.py`
  5. `python pipelines/test.py`
- Each should produce the same output and behavior as before the refactoring.
 