#!/usr/bin/env bash

set -euo pipefail

for attempt in {1..12}; do
  if curl --fail --silent --show-error \
    http://127.0.0.1:3000/api/health >/dev/null; then
    exit 0
  fi

  sleep 5
done

systemctl status coditude-frontend.service --no-pager || true
journalctl -u coditude-frontend.service --no-pager --lines 50 || true
exit 1
