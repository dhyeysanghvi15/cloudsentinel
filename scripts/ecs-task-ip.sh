#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

CLUSTER="$(cd "$TF_DIR" && terraform output -raw ecs_cluster_name)"
SERVICE="$(cd "$TF_DIR" && terraform output -raw ecs_service_name)"

TASK_ARN="$(aws ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" --desired-status RUNNING --query 'taskArns[0]' --output text)"
if [[ "$TASK_ARN" == "None" || -z "$TASK_ARN" ]]; then
  echo "No running task found."
  exit 1
fi

ENI_ID="$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)"
PUB_IP="$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" --query 'NetworkInterfaces[0].Association.PublicIp' --output text)"
echo "$PUB_IP"
