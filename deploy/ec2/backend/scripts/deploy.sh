#!/usr/bin/env bash

set -euo pipefail

APP_DIR="/opt/coditude/backend/current"
ENV_FILE="/etc/coditude-backend.env"
SERVICE_NAME="coditude-backend.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${LIFECYCLE_EVENT:-}" == "BeforeInstall" ]]; then
  systemctl stop "${SERVICE_NAME}" 2>/dev/null || true

  if ! id coditude >/dev/null 2>&1; then
    useradd --system --home-dir /opt/coditude --shell /sbin/nologin coditude
  fi

  install -d -o coditude -g coditude -m 0755 /opt/coditude/backend
  install -d -o coditude -g coditude -m 0755 /var/log/coditude
  rm -rf "${APP_DIR}"
  exit 0
fi

if [[ "${LIFECYCLE_EVENT:-}" != "ApplicationStart" ]]; then
  echo "Unsupported CodeDeploy event: ${LIFECYCLE_EVENT:-unknown}" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}." >&2
  exit 1
fi

for variable in DB_HOST DB_PORT DB_NAME DB_SECRET_ARN APP_ENV; do
  if ! grep --quiet "^${variable}=" "${ENV_FILE}"; then
    echo "Missing ${variable} in ${ENV_FILE}." >&2
    exit 1
  fi
done

python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/python" -m pip install \
  --requirement "${APP_DIR}/requirements.txt"

install -o root -g root -m 0644 \
  "${SCRIPT_DIR}/../systemd/${SERVICE_NAME}" \
  "/etc/systemd/system/${SERVICE_NAME}"

chown -R coditude:coditude /opt/coditude/backend /var/log/coditude
chmod 0600 "${ENV_FILE}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
