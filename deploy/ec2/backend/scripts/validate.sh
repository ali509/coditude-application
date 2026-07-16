#!/usr/bin/env bash

set -euo pipefail

for attempt in {1..18}; do
  if curl --fail --silent --show-error \
    http://127.0.0.1:8000/ready >/dev/null; then
    exit 0
  fi

  sleep 5
done

systemctl status coditude-backend.service --no-pager || true
journalctl -u coditude-backend.service --no-pager --lines 50 || true
exit 1
