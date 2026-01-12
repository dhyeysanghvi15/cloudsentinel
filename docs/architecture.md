# Architecture (MVP)

```mermaid
flowchart LR
  U[Recruiter / User] -->|Browser| CF[S3 Static Site (web)]
  CF -->|HTTPS| API[FastAPI (ECS Fargate)]
  API -->|Scan Snapshot JSON| S3[(S3 artifacts bucket)]
  API -->|Scan Metadata| DDB[(DynamoDB on-demand)]
  API -->|Events + Logs| CW[(CloudWatch Logs)]
  API -->|Read-only posture checks| AWS[(AWS APIs via boto3)]
  API -->|Safe simulations| AWS
  API -->|CloudTrail lookup| CT[(CloudTrail)]
```

Cost controls:
- No NAT Gateway, no RDS, no OpenSearch, no EKS.
- Fargate task size: `0.25 vCPU / 0.5GB`; ECS `desired_count=0` by default.
- CloudWatch log retention: 7 days.
- S3 artifacts lifecycle: expire after 30 days.
- Billing alarm in `us-east-1` for low threshold.

