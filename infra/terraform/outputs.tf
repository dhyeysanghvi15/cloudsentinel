output "name" {
  value = local.name
}

output "aws_region" {
  value = var.aws_region
}

output "artifact_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "scans_table" {
  value = aws_dynamodb_table.scans.name
}

output "ecr_repo_url" {
  value = aws_ecr_repository.api.repository_url
}

output "api_url" {
  value = "http://<run ./scripts/ecs-task-ip.sh>:8000"
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.api.name
}

output "web_url" {
  value = "http://${aws_s3_bucket.web.bucket}.s3-website-${var.aws_region}.amazonaws.com"
}

output "web_bucket" {
  value = aws_s3_bucket.web.bucket
}
