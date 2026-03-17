#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"
CONFIG_FILE="${SCRIPT_DIR}/airflow.env"

if [[ -f "${CONFIG_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "${CONFIG_FILE}"
  set +a
fi

: "${AIRFLOW_HOME:=${HOME}/airflow}"
: "${AIRFLOW_VENV:=${HOME}/airflow_venv}"
: "${AIRFLOW_BIN:=${AIRFLOW_VENV}/bin/airflow}"
: "${AIRFLOW_API_PORT:=8080}"
: "${INDIA_MARKET_PROJECT_DIR:=${PROJECT_ROOT}}"
: "${INDIA_MARKET_VENV:=${HOME}/india_market_venv}"
: "${INDIA_MARKET_PYTHON_BIN:=${INDIA_MARKET_VENV}/bin/python}"

RUN_DIR="${AIRFLOW_HOME}/local-run"
PID_DIR="${RUN_DIR}/pids"
LOG_DIR="${RUN_DIR}/logs"
DAG_SOURCE_PATH="${INDIA_MARKET_PROJECT_DIR}/airflow_dags/india_market_dag.py"
DAG_TARGET_DIR="${AIRFLOW_HOME}/dags"
DAG_TARGET_PATH="${DAG_TARGET_DIR}/india_market_dag.py"

export AIRFLOW_HOME
export AIRFLOW_VENV
export AIRFLOW_BIN
export AIRFLOW_API_PORT
export INDIA_MARKET_PROJECT_DIR
export INDIA_MARKET_VENV
export INDIA_MARKET_PYTHON_BIN

required_env_vars=(
  AIRFLOW__API_AUTH__JWT_SECRET
  AIRFLOW__API__SECRET_KEY
  AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS
)

ensure_directories() {
  mkdir -p "${PID_DIR}" "${LOG_DIR}" "${DAG_TARGET_DIR}"
}

ensure_required_env() {
  local missing=()
  local name
  for name in "${required_env_vars[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("${name}")
    fi
  done

  if (( ${#missing[@]} > 0 )); then
    printf "Missing required environment variables: %s\n" "${missing[*]}" >&2
    printf "Copy scripts/airflow/airflow.env.example to scripts/airflow/airflow.env and fill it in.\n" >&2
    exit 1
  fi
}

ensure_binaries() {
  if [[ ! -x "${AIRFLOW_BIN}" ]]; then
    printf "Airflow binary not found at %s\n" "${AIRFLOW_BIN}" >&2
    exit 1
  fi

  if [[ ! -x "${INDIA_MARKET_PYTHON_BIN}" ]]; then
    printf "Project Python binary not found at %s\n" "${INDIA_MARKET_PYTHON_BIN}" >&2
    exit 1
  fi
}

sync_dag() {
  if [[ ! -f "${DAG_SOURCE_PATH}" ]]; then
    printf "DAG source file not found at %s\n" "${DAG_SOURCE_PATH}" >&2
    exit 1
  fi

  cp "${DAG_SOURCE_PATH}" "${DAG_TARGET_PATH}"
}

pid_file() {
  printf "%s/%s.pid\n" "${PID_DIR}" "$1"
}

log_file() {
  printf "%s/%s.log\n" "${LOG_DIR}" "$1"
}

is_running() {
  local name="$1"
  local pid_path
  local pid

  pid_path="$(pid_file "${name}")"
  if [[ ! -f "${pid_path}" ]]; then
    return 1
  fi

  pid="$(<"${pid_path}")"
  if kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi

  rm -f "${pid_path}"
  return 1
}

start_component() {
  local name="$1"
  shift

  if is_running "${name}"; then
    printf "%s already running (pid %s)\n" "${name}" "$(<"$(pid_file "${name}")")"
    return 0
  fi

  nohup "$@" >>"$(log_file "${name}")" 2>&1 &
  echo $! >"$(pid_file "${name}")"
  printf "Started %s (pid %s)\n" "${name}" "$!"
}

stop_component() {
  local name="$1"
  local pid_path
  local pid

  pid_path="$(pid_file "${name}")"
  if [[ ! -f "${pid_path}" ]]; then
    printf "%s is not running\n" "${name}"
    return 0
  fi

  pid="$(<"${pid_path}")"
  if kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}"
    printf "Stopped %s (pid %s)\n" "${name}" "${pid}"
  else
    printf "%s was not running\n" "${name}"
  fi

  rm -f "${pid_path}"
}

print_component_status() {
  local name="$1"
  if is_running "${name}"; then
    printf "%-14s running (pid %s) log=%s\n" "${name}" "$(<"$(pid_file "${name}")")" "$(log_file "${name}")"
  else
    printf "%-14s stopped log=%s\n" "${name}" "$(log_file "${name}")"
  fi
}

bootstrap() {
  ensure_directories
  ensure_required_env
  ensure_binaries
  sync_dag
}
