#!/usr/bin/env bash

set -euo pipefail

if systemctl list-unit-files coditude-frontend.service >/dev/null 2>&1; then
  systemctl stop coditude-frontend.service || true
fi

if ! id coditude >/dev/null 2>&1; then
  useradd --system --home-dir /opt/coditude --shell /sbin/nologin coditude
fi

install -d -o coditude -g coditude -m 0755 /opt/coditude/frontend
install -d -o coditude -g coditude -m 0755 /var/log/coditude
rm -rf /opt/coditude/frontend/current
