# cloudsentinel

“Interactive AWS cloud security posture + detection lab with IAM policy doctor, attack simulation, and remediation workflows.”

## What it is
- A recruiter-facing, lab-only security project for **your own AWS account**.
- FastAPI backend runs posture checks, validates IAM policies, and generates safe CloudTrail telemetry.
- Next.js UI provides an interactive dashboard and workflows.

## Skills demonstrated
- AWS IAM + least privilege, Access Analyzer policy validation (when available)
- AWS CloudTrail event timeline + detection thinking
- S3 + DynamoDB storage patterns (low-cost, on-demand)
- Containerized FastAPI → ECS Fargate (public-only VPC, no NAT)
- Terraform IaC + cost safeguards + teardown discipline

## Architecture
```mermaid
flowchart LR
  U[User] -->|Browser| WEB[S3 static site (Next.js export)]
  U -->|HTTP| API[FastAPI on ECS Fargate\n(public task IP; dev/demo mode)]
  API --> S3[(S3 artifacts: scan snapshots)]
  API --> DDB[(DynamoDB: scan metadata)]
  API --> CW[(CloudWatch Logs 7d retention)]
  API --> AWS[(AWS APIs via boto3)]
  API --> CT[(CloudTrail lookup)]
```

## Run locally in 2 minutes
1. `cp .env.example .env`
2. `make dev` (API + DynamoDB local)
3. In another terminal: `make web`
4. Open `http://localhost:3000` (set API base via `NEXT_PUBLIC_API_BASE_URL` if needed)

## Deploy to AWS (dev)
Prereqs: Docker, Terraform, AWS CLI credentials.

1. `make deploy-dev`
2. `make start-dev`
3. `./scripts/ecs-task-ip.sh` → API IP (dev/demo mode; no ALB)
4. API URL: `http://<ip>:8000`

Frontend (S3 static export):
- Build: `cd web && npm install && npm run export`
- Upload: `make deploy-web API_BASE_URL=http://<ip>:8000`
- Get URL: `cd infra/terraform && terraform output -raw web_url`

## Cost controls (explicit)
- No NAT Gateway.
- No RDS / OpenSearch / EKS.
- ECS service `desired_count=0` by default; start only when needed.
- Smallest practical Fargate size: `256 CPU / 512 MiB`.
- CloudWatch log retention: 7 days.
- S3 artifacts lifecycle expiration: 30 days.
- Billing alarm: `$10` estimated charges (us-east-1).

## AWS resources created (dev)
- VPC (public-only) + 2 public subnets + IGW + route tables
- ECS cluster + task definition + service (Fargate)
- ECR repo (with lifecycle policy keeping last 10 images)
- S3 artifacts bucket (private, SSE-S3, 30-day expiration)
- DynamoDB table (on-demand)
- S3 website bucket (public read; dev-only)
- CloudWatch log group (7-day retention)
- CloudWatch billing alarm + SNS topic (optional email subscription)

## Cost estimate (rough)
- Idle (service stopped, desiredCount=0): ~$0–$2/mo (S3+DDB storage/requests + minimal logs; depends on usage)
- While running 1 task: Fargate compute + logs (typically a few $/month if run a few hours/week; stop when done)

## Teardown
- `make stop-dev`
- `make destroy-dev`

## Demo GIF
- Record a short run (Dashboard scan → Policy Doctor → Simulator timeline) and save to `docs/demo.gif`.
- Embed it near the top of this README for maximum recruiter impact.

## Security & ethics
- Lab-only: run in a dedicated dev AWS account you own.
- Simulations create tagged resources with prefix `cloudsentinel-sim-*` and include cleanup.
