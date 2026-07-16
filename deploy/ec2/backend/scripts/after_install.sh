#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="${SCRIPT_DIR}/../systemd/coditude-backend.service"
APP_DIR="/opt/coditude/backend/current"
ENV_FILE="/etc/coditude-backend.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}; infrastructure must provide database settings." >&2
  exit 1
fi

for variable in DB_HOST DB_PORT DB_NAME DB_USERNAME DB_PASSWORD APP_ENV; do
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
  "${SERVICE_FILE}" \
  /etc/systemd/system/coditude-backend.service

chown -R coditude:coditude /opt/coditude/backend /var/log/coditude
chmod 0600 "${ENV_FILE}"

systemctl daemon-reload
systemctl enable coditude-backend.service
