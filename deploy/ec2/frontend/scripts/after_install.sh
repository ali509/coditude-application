#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="${SCRIPT_DIR}/../systemd/coditude-frontend.service"
ENV_FILE="/etc/coditude-frontend.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}; infrastructure must provide BACKEND_URL." >&2
  exit 1
fi

if [[ ! -f /opt/coditude/frontend/current/server.js ]]; then
  echo "Frontend standalone artifact is missing server.js." >&2
  exit 1
fi

install -o root -g root -m 0644 \
  "${SERVICE_FILE}" \
  /etc/systemd/system/coditude-frontend.service

chown -R coditude:coditude /opt/coditude/frontend /var/log/coditude
chmod 0600 "${ENV_FILE}"

systemctl daemon-reload
systemctl enable coditude-frontend.service
