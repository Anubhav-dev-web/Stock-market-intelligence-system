#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/common.sh"

bootstrap

start_component "scheduler" "${AIRFLOW_BIN}" scheduler
start_component "dag_processor" "${AIRFLOW_BIN}" dag-processor
start_component "api_server" "${AIRFLOW_BIN}" api-server --port "${AIRFLOW_API_PORT}"

printf "\nAirflow UI: http://localhost:%s\n" "${AIRFLOW_API_PORT}"
printf "Check status with: bash scripts/airflow/status.sh\n"
