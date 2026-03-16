from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

PROJECT_DIR = "/home/maximus/india_market"
PYTHON_BIN  = "/home/maximus/airflow_venv/bin/python"

default_args = {
    'owner':             'india-market',
    'retries':           2,
    'retry_delay':       timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
    'email_on_failure':  False,
}

with DAG(
    dag_id            = 'india_market_daily',
    default_args      = default_args,
    description       = 'Daily NSE refresh after market close',
    schedule_interval = '30 10 * * 1-5',
    start_date        = datetime(2026, 3, 15),
    catchup           = False,
    tags              = ['india', 'nse', 'production'],
) as dag:

    t1 = BashOperator(
        task_id      = 'fetch_latest_prices',
        bash_command = f'cd {PROJECT_DIR} && {PYTHON_BIN} pipelines/daily_refresh.py',
    )

    t2 = BashOperator(
        task_id      = 'compute_indicators',
        bash_command = f'cd {PROJECT_DIR} && {PYTHON_BIN} pipelines/compute_indicators.py',
    )

    t3 = BashOperator(
        task_id      = 'create_views',
        bash_command = f'cd {PROJECT_DIR} && {PYTHON_BIN} pipelines/create_views.py',
    )

    t1 >> t2 >> t3