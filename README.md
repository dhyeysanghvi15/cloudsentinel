# cloudsentinel

Interactive cloud security posture + detection lab (demo-ready on GitHub Pages, full mode via localhost). 🔐

## Live Demo (GitHub Pages)

- `https://dhyeysanghvi15.github.io/cloudsentinel/` (no backend, fully interactive)
- Runs locally in ~2 minutes: `make dev` + `make web`

## What you’ll see in 60 seconds ⚡

- Open **Dashboard** → see score, domain breakdown, top risks, and trend.
- Go to **Scans** → compare the last two snapshots (improved vs regressed).
- Paste an IAM policy into **Policy Doctor** → get findings + rewrite hints instantly.
- Run **Simulator** scenarios → watch the detection timeline populate like real telemetry.

## Modes

- **Demo Mode (default on Pages):** bundled sample data (`web/public/demo/*`) + localStorage; no backend.
- **Local Mode (localhost):** FastAPI + SQLite persistence in `./data/cloudsentinel.db`.
- **Optional read-only AWS mode (local only):** set `AWS_SCAN_ENABLED=true` to run *read-only* boto3 checks against your own account; no resources created, and it fails closed.

## Features

- **Posture scoring & checks:** transparent scoring (`pass=1`, `warn=0.5`, `fail=0`) with evidence + recommendations.
- **IAM Policy Doctor:** paste JSON → validation + safety-oriented hints (local heuristics; optional Access Analyzer if enabled).
- **Timeline / Simulator:** demo replay on Pages; local timeline store + scenario runner on localhost.
- **Scan history + diffs:** compare snapshots to show improvements/regressions over time.

## Skills I’m demonstrating (as proof)

- Designing CSPM checks with severity, evidence, and remediation guidance (not just “pass/fail”).
- Building detection narratives: how timeline events become signals and triage workflows.
- IAM policy risk analysis UX (fast feedback loops; safe defaults; least-privilege framing).
- Product-quality delivery: static export + GitHub Pages + local backend + persistence.

## Run locally

```bash
cp .env.example .env

# Terminal A (API): starts FastAPI on http://localhost:8000
make dev

# Terminal B (Web): starts Next.js dev server on http://localhost:3000
make web
```

In the UI header: **Mode → Local API (localhost:8000)**.

## Deploy (GitHub Pages)

GitHub Pages publishes automatically on every push to `main` via:
- Workflow: `deploy-pages` (`.github/workflows/pages.yml`)
- Build: Next.js static export with `NEXT_PUBLIC_BASE_PATH="/cloudsentinel"` → artifact `web/out`

## $0 AWS bill guarantee (explicit)

**No Terraform apply. No AWS resources.** Demo Mode is backend-free, and Local Mode runs entirely on localhost.

Optional AWS scanning is:
- disabled by default (`AWS_SCAN_ENABLED=false`)
- read-only by design
- intended only for your own AWS account credentials on your machine

Minimal read-only IAM policy (example for the scanning principal):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["sts:GetCallerIdentity"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["iam:GetAccountSummary", "iam:GetAccountPasswordPolicy", "iam:ListUsers", "iam:ListAccessKeys", "iam:ListRoles", "iam:ListAttachedUserPolicies", "iam:ListAttachedRolePolicies"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["ec2:DescribeSecurityGroups"], "Resource": "*" }
  ]
}
```

## Architecture

- `docs/architecture.md` (Demo Mode vs Local Mode diagram + data flow)

## Repo map

- `web/` — Next.js UI (static export + GitHub Pages Demo Mode)
- `web/public/demo/` — bundled demo JSON (scans, timeline, policy examples)
- `api/` — FastAPI backend (localhost-only) + SQLite storage
- `docs/` — architecture, demo script, threat model
- `.github/workflows/pages.yml` — Pages deploy
- `.github/workflows/ci.yml` — CI (API lint/tests + web build)

## Screenshots / GIF

Record a quick walkthrough (Dashboard → Scans diff → Policy Doctor → Simulator) and save it as `docs/demo.gif`.

## Security & ethics

Lab-only. Don’t point scanning at accounts you don’t own or have explicit permission to test.
