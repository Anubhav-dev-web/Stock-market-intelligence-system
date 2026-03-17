#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/common.sh"

ensure_directories

printf "Airflow home: %s\n" "${AIRFLOW_HOME}"
printf "Project dir : %s\n" "${INDIA_MARKET_PROJECT_DIR}"
printf "Python bin  : %s\n" "${INDIA_MARKET_PYTHON_BIN}"
printf "DAG file    : %s\n\n" "${DAG_TARGET_PATH}"

print_component_status "scheduler"
print_component_status "dag_processor"
print_component_status "api_server"
