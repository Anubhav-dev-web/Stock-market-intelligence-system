# Start Project Commands

This file is the quick command sheet for starting and running the India market ETL project.

Use `end_to_end_guide.md` when you want the full explanation. Use this file when you just need the terminal commands.

## 1. Open the Project Folder

### Windows PowerShell

Run this in Windows PowerShell:

```powershell
cd D:\DataAnalyst\MKT-1
```

### WSL or Ubuntu

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
```

## 2. Check the `.env` File

The project expects `.env` in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=india_market
DB_USER=postgres
DB_PASSWORD=your_password
```

Make sure PostgreSQL is running before you run the pipeline.

## 3. Activate the Project Environment

### Windows PowerShell

If the `venv` folder already exists:

Run this in Windows PowerShell from `D:\DataAnalyst\MKT-1`:

```powershell
venv\Scripts\activate
```

If you need to create it again:

Run this in Windows PowerShell from `D:\DataAnalyst\MKT-1`:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### WSL or Ubuntu

If the `venv` folder already exists:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
source venv/bin/activate
```

If you need to create it again:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. First-Time Full Project Run

Run these once for a fresh database:

Run this in the terminal where your project environment is activated.

```bash
python pipelines/create_everything.py
python pipelines/setup_and_load.py
python pipelines/setup_dimensions.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/test.py
```

Optional repair command for older databases:

Run this in the terminal where your project environment is activated.

```bash
python pipelines/fix_dim_dates.py
```

## 5. Normal Daily Manual Run

Use this after the first setup is complete:

Run this in the terminal where your project environment is activated.

```bash
python pipelines/daily_refresh.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
python pipelines/test.py
```

## 6. Airflow Setup

Airflow is usually cleaner in WSL or Ubuntu with its own virtual environment.

From the project folder:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
python3 -m venv ~/airflow_venv
source ~/airflow_venv/bin/activate
pip install -r requirements-airflow.txt
```

Create a separate Linux project environment for Airflow tasks:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
python3 -m venv ~/india_market_venv
source ~/india_market_venv/bin/activate
pip install -r requirements.txt
```

Create the Airflow environment config:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
cp scripts/airflow/airflow.env.example scripts/airflow/airflow.env
nano scripts/airflow/airflow.env
```

Example values:

```bash
export AIRFLOW_HOME="$HOME/airflow"
export AIRFLOW_VENV="$HOME/airflow_venv"
export AIRFLOW_API_PORT="8080"

export INDIA_MARKET_PROJECT_DIR="/mnt/d/DataAnalyst/MKT-1"
export INDIA_MARKET_VENV="$HOME/india_market_venv"
export INDIA_MARKET_PYTHON_BIN="$INDIA_MARKET_VENV/bin/python"

export AIRFLOW__API_AUTH__JWT_SECRET="replace-with-a-random-secret"
export AIRFLOW__API__SECRET_KEY="replace-with-a-second-random-secret"
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS="admin:admin"
```

If your project environment is somewhere else, update `INDIA_MARKET_VENV` and `INDIA_MARKET_PYTHON_BIN`.

## 7. Start, Check, and Stop Airflow

Start Airflow:

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
bash scripts/airflow/start.sh
```

Open the Airflow UI:

```text
http://localhost:8080
```

Show the generated Airflow login password:

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
source scripts/airflow/airflow.env
cat "$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated"
```

Check Airflow processes:

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
bash scripts/airflow/status.sh
```

Stop Airflow:

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
bash scripts/airflow/stop.sh
```

## 8. Useful Airflow Commands

List DAGs:

Run this in WSL or Ubuntu terminal:

```bash
source ~/airflow_venv/bin/activate
airflow dags list
```

Check DAG import errors:

Run this in WSL or Ubuntu terminal:

```bash
source ~/airflow_venv/bin/activate
airflow dags list-import-errors
```

Trigger the project DAG manually:

Run this in WSL or Ubuntu terminal:

```bash
source ~/airflow_venv/bin/activate
airflow dags trigger india_market_daily
```

## 9. Quick Troubleshooting

If Python says dependencies do not match:

Run this in the terminal where your project environment is activated.

```bash
pip install -r requirements.txt
```

If an Airflow task fails with `ModuleNotFoundError` for a project package:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
cd /mnt/d/DataAnalyst/MKT-1
source ~/india_market_venv/bin/activate
pip install -r requirements.txt
python -c "import google.generativeai; print('Gemini package OK')"
```

Airflow tasks run with `~/india_market_venv/bin/python`, not the Windows `venv`.

If Airflow cannot find the project Python:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
source scripts/airflow/airflow.env
echo "$INDIA_MARKET_PYTHON_BIN"
```

Then verify this path exists:

Run this in the same WSL or Ubuntu terminal:

```bash
ls -l "$INDIA_MARKET_PYTHON_BIN"
```

If the DAG does not appear in Airflow:

Run this in WSL or Ubuntu terminal from `/mnt/d/DataAnalyst/MKT-1`:

```bash
bash scripts/airflow/status.sh
source ~/airflow_venv/bin/activate
airflow dags list-import-errors
```

If you edited `airflow_dags/india_market_dag.py` but the UI still shows the old task list:

Run this in WSL or Ubuntu terminal:

```bash
cd /mnt/d/DataAnalyst/MKT-1
bash scripts/airflow/stop.sh
bash scripts/airflow/start.sh
source ~/airflow_venv/bin/activate
airflow tasks list india_market_daily
airflow dags list-import-errors
```

If raw data exists but analytics tables are empty:

Run this in the terminal where your project environment is activated.

```bash
python pipelines/setup_dimensions.py
python pipelines/compute_indicators.py
python pipelines/create_views.py
```
