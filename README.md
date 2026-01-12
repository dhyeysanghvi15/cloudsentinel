# cloudsentinel

Interactive cloud security posture + detection lab (demo-ready on GitHub Pages, full mode via localhost).

## Live Demo (no backend)

- GitHub Pages: `https://<github-username>.github.io/cloudsentinel/`

## What you can click through

- **Dashboard:** posture score + domain breakdown + top risks + trend
- **Scans:** scan history + diff (improved/regressed) + scan detail
- **Policy Doctor:** paste IAM policy JSON → findings + rewrite hints
- **Simulator:** replay “attack-like” actions → see a realistic detection timeline

## $0 AWS bill guarantee (explicit)

- This repo does **not** deploy anything to AWS.
- This repo does **not** run `terraform apply` and does **not** create AWS resources (VPC/ECS/S3/DynamoDB/CloudTrail trails/etc).
- Demo Mode works entirely from bundled sample data on GitHub Pages.
- Local Mode stores everything on your machine (SQLite in `./data/`).
- Optional AWS scanning is **read-only** and **disabled by default**.

## Skills demonstrated

- Cloud security posture thinking (what to check, how to score, how to prioritize)
- Detection engineering UX (timeline, scenarios, “what happened” narrative)
- IAM policy analysis UX (fast feedback, guardrails, rewrite hints)
- Full-stack engineering (Next.js static export + FastAPI + SQLite + GitHub Actions Pages)

## Run locally (2 minutes)

1. `cp .env.example .env`
2. Terminal A (API): `make dev` → `http://localhost:8000/health`
3. Terminal B (web): `make web` → open `http://localhost:3000`
4. In the UI header, set **Mode → Local API (localhost:8000)**.

## Optional: enable read-only AWS scan (still $0 if you don’t deploy)

1. Set `AWS_SCAN_ENABLED=true` in your `.env`
2. Run `make dev`
3. Run a scan from the Dashboard

Minimal read-only IAM policy (example):
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

- `docs/architecture.md`

## Demo media

- Record a short run (Dashboard → Scans diff → Policy Doctor → Simulator timeline) and save to `docs/demo.gif`.
