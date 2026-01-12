#!/usr/bin/env bash
set -euo pipefail

echo "This repo intentionally does NOT support AWS deployments (guaranteed $0 AWS bill)." >&2
echo "Use Local Mode: make dev + make web." >&2
exit 1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

CLUSTER="$(cd "$TF_DIR" && terraform output -raw ecs_cluster_name)"
SERVICE="$(cd "$TF_DIR" && terraform output -raw ecs_service_name)"

aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --desired-count 1 >/dev/null
echo "Started ECS service desiredCount=1."
echo "Get public task IP with: ./scripts/ecs-task-ip.sh"
