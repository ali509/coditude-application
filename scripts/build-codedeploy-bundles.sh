#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/build/codedeploy"
FRONTEND_DIR="${ROOT_DIR}/apps/frontend"
BACKEND_DIR="${ROOT_DIR}/apps/backend"

rm -rf "${BUILD_DIR}"
mkdir -p \
  "${BUILD_DIR}/frontend/artifact" \
  "${BUILD_DIR}/backend/artifact"

pushd "${FRONTEND_DIR}" >/dev/null
npm ci
npm run build
popd >/dev/null

cp -R "${FRONTEND_DIR}/.next/standalone/." \
  "${BUILD_DIR}/frontend/artifact/"
mkdir -p "${BUILD_DIR}/frontend/artifact/.next"
cp -R "${FRONTEND_DIR}/.next/static" \
  "${BUILD_DIR}/frontend/artifact/.next/static"
cp -R "${FRONTEND_DIR}/public" \
  "${BUILD_DIR}/frontend/artifact/public"
cp -R "${ROOT_DIR}/deploy/ec2/frontend/." \
  "${BUILD_DIR}/frontend/"

cp -R "${BACKEND_DIR}/app" "${BUILD_DIR}/backend/artifact/app"
cp "${BACKEND_DIR}/requirements.txt" \
  "${BUILD_DIR}/backend/artifact/requirements.txt"
find "${BUILD_DIR}/backend/artifact" \
  -type d -name __pycache__ -prune -exec rm -rf {} +
find "${BUILD_DIR}/backend/artifact" \
  -type f -name "*.pyc" -delete
cp -R "${ROOT_DIR}/deploy/ec2/backend/." \
  "${BUILD_DIR}/backend/"

find "${BUILD_DIR}" -path "*/scripts/*.sh" -exec chmod 0755 {} +

(
  cd "${BUILD_DIR}/frontend"
  zip -q -r ../coditude-frontend.zip .
)

(
  cd "${BUILD_DIR}/backend"
  zip -q -r ../coditude-backend.zip .
)

printf 'Created:\n'
printf '  %s\n' \
  "${BUILD_DIR}/coditude-frontend.zip" \
  "${BUILD_DIR}/coditude-backend.zip"
