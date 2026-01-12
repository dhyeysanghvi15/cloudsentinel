# Threat Model (Lab-only)

## Assets
- AWS account telemetry (CloudTrail events).
- Scan artifacts (JSON snapshots) stored in S3.
- Scan metadata in DynamoDB.

## Primary risks
- Over-permissioned scanning role.
- Accidental creation of costly resources.
- Attack simulations impacting real resources.

## Mitigations
- Explicit cost controls: no NAT/RDS/OpenSearch/EKS; ECS desiredCount=0 by default.
- Simulations use dedicated prefixes + tags and have automatic cleanup.
- Log retention set to 7 days; artifacts lifecycle expiration 30 days.
- IAM policy doctor encourages least-privilege and safe conditions.

