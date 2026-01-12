#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT/infra/terraform"

TAG="${IMAGE_TAG:-$(date +%Y%m%d%H%M%S)}"

echo "==> Terraform init/apply (creates low-cost infra; ECS desired_count=0 by default)"
(cd "$TF_DIR" && terraform init -input=false)
(cd "$TF_DIR" && terraform apply -input=false -auto-approve -var "image_tag=$TAG")

ECR_URL="$(cd "$TF_DIR" && terraform output -raw ecr_repo_url)"
AWS_REGION="$(cd "$TF_DIR" && terraform output -raw aws_region)"

echo "==> Build + push API image: $ECR_URL:$TAG"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ECR_URL%/*}"
docker build -t "$ECR_URL:$TAG" "$ROOT/api"
docker push "$ECR_URL:$TAG"

echo "==> Terraform apply (registers task definition with image)"
(cd "$TF_DIR" && terraform apply -input=false -auto-approve -var "image_tag=$TAG")

echo "==> Done. Use 'make start-dev' to run 1 task (or set desired_count=1)."
