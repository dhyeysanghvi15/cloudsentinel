#!/usr/bin/env bash
set -euo pipefail

echo "This repo intentionally does NOT support AWS deployments (guaranteed $0 AWS bill)." >&2
echo "GitHub Pages is deployed via GitHub Actions; Local Mode runs on localhost." >&2
exit 1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

API_BASE_URL="${1:-}"
if [[ -z "$API_BASE_URL" ]]; then
  echo "Usage: ./scripts/deploy-web.sh http://<api-ip>:8000"
  exit 1
fi

WEB_BUCKET="$(cd "$TF_DIR" && terraform output -raw web_bucket)"

echo "==> Build static web with NEXT_PUBLIC_API_BASE_URL=$API_BASE_URL"
(cd "$ROOT/web" && NEXT_PUBLIC_API_BASE_URL="$API_BASE_URL" npm install && npm run export)

echo "==> Upload to s3://$WEB_BUCKET"
aws s3 sync "$ROOT/web/out" "s3://$WEB_BUCKET" --delete

echo "==> Web URL:"
(cd "$TF_DIR" && terraform output -raw web_url)
