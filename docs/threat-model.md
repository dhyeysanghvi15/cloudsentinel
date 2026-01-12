# Threat Model (Local-first)

## Assets
- Local scan snapshots (stored in SQLite under `./data/`).
- Local simulator timeline events (stored in SQLite under `./data/`).
- Pasted policy JSON in the browser (Policy Doctor UI).

## Primary risks
- Running untrusted policies or scans against a real environment without reviewing permissions.
- Exposing the local API to the internet (CORS/origin misconfig).
- Confusing demo data for real findings.

## Mitigations
- **$0 AWS bill default:** `AWS_SCAN_ENABLED=false` and no AWS deployments in this repo.
- Local Mode stores data on disk only; no cloud dependencies.
- Demo Mode banner is always visible when using bundled data.
- Optional AWS scanning is intended to be **read-only** (principle of least privilege).
