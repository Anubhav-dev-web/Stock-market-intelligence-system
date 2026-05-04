import os
import shlex
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

PROJECT_DIR = Path(os.getenv("INDIA_MARKET_PROJECT_DIR", Path(__file__).resolve().parents[1]))
PYTHON_BIN = os.getenv("INDIA_MARKET_PYTHON_BIN", sys.executable)


def command(script_name: str) -> str:
    project_dir = shlex.quote(str(PROJECT_DIR))
    python_bin = shlex.quote(PYTHON_BIN)
    script_path = shlex.quote(f"pipelines/{script_name}")
    return f"cd {project_dir} && {python_bin} {script_path}"


default_args = {
    "owner": "india-market",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="india_market_daily",
    default_args=default_args,
    description="Daily NSE refresh after market close",
    schedule="30 10 * * 1-5",
    start_date=datetime(2026, 3, 15),
    catchup=False,
    tags=["india", "nse", "production"],
) as dag:

    fetch_latest_prices = BashOperator(
        task_id="fetch_latest_prices",
        bash_command=command("daily_refresh.py"),
    )

    compute_indicators = BashOperator(
        task_id="compute_indicators",
        bash_command=command("compute_indicators.py"),
    )

    create_views = BashOperator(
        task_id="create_views",
        bash_command=command("create_views.py"),
    )

    generate_ai_commentary = BashOperator(
        task_id="generate_ai_commentary",
        bash_command=command("ai_commentary.py"),
    )

    fetch_latest_prices >> compute_indicators >> create_views >> generate_ai_commentary