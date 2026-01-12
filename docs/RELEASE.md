# Release

This repo is designed to be **demo-ready without any backend** (GitHub Pages) and **fully functional locally** (FastAPI + SQLite).

## What’s included

- **Demo Mode (GitHub Pages):** bundled demo JSON + interactive UI (no backend).
- **Local Mode (localhost):** FastAPI API + SQLite persistence in `./data/cloudsentinel.db`.
- **Optional read-only AWS scan (local only):** `AWS_SCAN_ENABLED=true` enables read-only boto3 checks against your own account.

## $0 AWS bill guarantee

- No Terraform apply.
- No AWS resources created by this repo.
- Optional AWS scanning is **read-only**, **local-only**, and **disabled by default**.

## How to verify (release gate)

From repo root:

```bash
make lint
make test
make web-build
rg -n "localhost:8000|127\\.0\\.0\\.1:8000" web/out -S || true
```

## How to run locally

```bash
cp .env.example .env
make dev
make web
```

In the UI header: switch **Mode → Local API**.

