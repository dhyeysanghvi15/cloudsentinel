#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

echo "==> Stopping ECS service to avoid stray tasks"
if terraform -chdir="$TF_DIR" output -raw ecs_cluster_name >/dev/null 2>&1; then
  CLUSTER="$(cd "$TF_DIR" && terraform output -raw ecs_cluster_name)"
  SERVICE="$(cd "$TF_DIR" && terraform output -raw ecs_service_name)"
  aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --desired-count 0 >/dev/null || true
fi

echo "==> Terraform destroy"
(cd "$TF_DIR" && terraform destroy -auto-approve)

