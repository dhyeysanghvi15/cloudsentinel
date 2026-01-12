# cloudsentinel

Interactive cloud security posture + detection lab — **demo-ready on GitHub Pages, full mode on localhost**. 🛡️

[Live Demo](https://dhyeysanghvi15.github.io/cloudsentinel/) • [Run Locally](#run-locally) • [Modes](#modes) • [Proof](#proof-of-engineering) • [Build--ship-pages](#build--ship-pages) • [Guarantee](#0-aws-bill-guarantee)

---

[![CI](https://github.com/dhyeysanghvi15/cloudsentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/dhyeysanghvi15/cloudsentinel/actions/workflows/ci.yml)
[![Deploy Pages](https://github.com/dhyeysanghvi15/cloudsentinel/actions/workflows/pages.yml/badge.svg)](https://github.com/dhyeysanghvi15/cloudsentinel/actions/workflows/pages.yml)
[![License](https://img.shields.io/github/license/dhyeysanghvi15/cloudsentinel)](LICENSE)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)
![AWS bill](https://img.shields.io/badge/AWS%20bill-%240%20guarantee-111827?logo=amazonaws&logoColor=white)

## Live Demo ☁️

**GitHub Pages:** https://dhyeysanghvi15.github.io/cloudsentinel/  
No backend. Click around immediately.

**Runs locally in 2 minutes:**
```bash
cp .env.example .env
make dev
make web
```

## What you’ll see in 60 seconds ⚡

<details open>
<summary><strong>Click path (start-to-finish)</strong></summary>

1) **Dashboard** → posture score + domain breakdown + trend  
2) **Scans** → compare two snapshots (improved vs regressed)  
3) **Policy Doctor** → paste IAM policy JSON → findings + rewrite hints  
4) **Simulator** → run scenarios → see a realistic detection timeline  
5) **Mode switcher** (header) → flip Demo / Local API / Custom API  

</details>

## Modes

<details open>
<summary><strong>Demo Mode (default on GitHub Pages)</strong></summary>

- Uses bundled sample data from `web/public/demo/*` + localStorage.
- Works with **zero backend**.
- Banner shown in-app (verbatim):  
  **“Demo Mode: bundled sample data. Run locally for full features.”**

</details>

<details>
<summary><strong>Local Mode (FastAPI on localhost)</strong></summary>

- Backend: `http://localhost:8000`
- Persistence: `./data/cloudsentinel.db` (SQLite)
- In the UI header: **Mode → Local API**

</details>

<details>
<summary><strong>Optional Read-only AWS Mode (local only)</strong></summary>

- Disabled by default: `AWS_SCAN_ENABLED=false`
- If enabled, it performs **read-only** boto3 calls against **your** AWS account credentials.
- No resources created; if credentials are missing, it fails closed and falls back safely.

</details>

## Core Features ✅

| Feature | Why it matters | Where |
|---|---|---|
| Posture score + domains | Prioritizes what to fix first | `/dashboard` |
| Scan history + diffs | Shows regressions/improvements over time | `/scans` |
| IAM Policy Doctor | Faster + safer policy iteration | `/policy-doctor` |
| Timeline / Simulator | Turns actions into “detection thinking” | `/simulator` |
| API-down fallback | Keeps the experience usable in Demo Mode | toast + **Switch to Demo Mode** |

## Proof of engineering

<details>
<summary><strong>Show internals (API, storage, export, CI)</strong></summary>

**API endpoints**
- `GET /health`
- `POST /api/scan`
- `GET /api/scans`
- `GET /api/scans/{scan_id}`
- `GET /api/score/latest`
- `POST /api/policy/validate`
- `POST /api/simulate/{scenario}`
- `POST /api/simulate/cleanup`
- `GET /api/timeline?since=...`

**Storage model**
- Local persistence only: SQLite at `./data/cloudsentinel.db`

**Export behavior (GitHub Pages)**
- Next.js static export: `output: "export"`
- Repo base path: `/cloudsentinel` (assets + routes)
- Demo data is shipped inside the export: `web/out/demo/*.json`

**CI workflows**
- `.github/workflows/ci.yml` — API lint/tests + web lint/build
- `.github/workflows/pages.yml` — builds `web/out` and deploys GitHub Pages

</details>

## Run locally

```bash
cp .env.example .env
make dev
make web
```

Open `http://localhost:3000` → header → **Mode → Local API**.

## Build + ship (Pages)

- GitHub Actions builds a static export into `web/out` and deploys to GitHub Pages.
- Workflow files:
  - `.github/workflows/pages.yml`
  - `.github/workflows/ci.yml`

## $0 AWS bill guarantee

**No Terraform apply. No AWS resources created.**

- Demo Mode: zero backend.
- Local Mode: localhost-only + local SQLite.
- Optional AWS scanning: **read-only**, **local-only**, **off by default**.

## Repo map

```text
cloudsentinel/
  api/        # FastAPI backend (localhost)
  web/        # Next.js UI (static export + Pages demo)
  docs/       # architecture + release notes
  scripts/    # legacy AWS scripts are intentionally hard-disabled
```

## Security & ethics

Lab-only. Don’t scan accounts you don’t own or have explicit permission to test.
