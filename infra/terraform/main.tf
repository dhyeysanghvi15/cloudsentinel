resource "random_id" "suffix" {
  byte_length = 2
}

locals {
  name = "${var.name_prefix}-${random_id.suffix.hex}"
  tags = {
    Project = "cloudsentinel"
    Env     = "dev"
    Owner   = var.owner
  }
}

# --- S3 artifacts ---
resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name}-artifacts"
  force_destroy = true
  tags   = local.tags
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    id     = "expire-scan-artifacts"
    status = "Enabled"
    expiration {
      days = 30
    }
    filter { prefix = "scans/" }
  }
}

# --- DynamoDB (on-demand) ---
resource "aws_dynamodb_table" "scans" {
  name         = "${local.name}-scans"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "scan_id"

  attribute {
    name = "scan_id"
    type = "S"
  }

  tags = local.tags
}

# --- ECR ---
resource "aws_ecr_repository" "api" {
  name                 = "${local.name}-api"
  image_tag_mutability = "MUTABLE"
  tags                 = local.tags
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}

# --- Networking (public-only VPC; NO NAT) ---
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = merge(local.tags, { Name = "${local.name}-vpc" })
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = merge(local.tags, { Name = "${local.name}-igw" })
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags                    = merge(local.tags, { Name = "${local.name}-public-${count.index}" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = merge(local.tags, { Name = "${local.name}-public-rt" })
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# --- CloudWatch logs (7 days retention) ---
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name}-api"
  retention_in_days = 7
  tags              = local.tags
}

# --- ECS ---
resource "aws_ecs_cluster" "main" {
  name = "${local.name}-cluster"
  tags = local.tags
}

resource "aws_security_group" "api" {
  name        = "${local.name}-api-sg"
  description = "cloudsentinel api ingress"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.api_ingress_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

data "aws_iam_policy_document" "task_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${local.name}-task-exec"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "task_exec" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name               = "${local.name}-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume.json
  tags               = local.tags
}

data "aws_iam_policy_document" "task_policy" {
  statement {
    sid = "Artifacts"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.artifacts.arn,
      "${aws_s3_bucket.artifacts.arn}/*"
    ]
  }

  statement {
    sid       = "ScansTable"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Scan"]
    resources = [aws_dynamodb_table.scans.arn]
  }

  statement {
    sid = "ReadOnlyChecks"
    actions = [
      "sts:GetCallerIdentity",
      "iam:GetAccountSummary",
      "iam:GetAccountPasswordPolicy",
      "iam:ListUsers",
      "iam:ListRoles",
      "iam:ListAccessKeys",
      "iam:ListAttachedUserPolicies",
      "iam:ListAttachedRolePolicies",
      "cloudtrail:DescribeTrails",
      "cloudtrail:GetTrailStatus",
      "cloudtrail:LookupEvents",
      "logs:DescribeLogGroups",
      "ec2:DescribeSecurityGroups",
      "s3:ListAllMyBuckets",
      "s3:GetBucketPublicAccessBlock",
      "s3:GetEncryptionConfiguration",
      "s3:GetBucketLogging",
      "kms:ListKeys",
      "kms:GetKeyPolicy",
      "config:DescribeConfigurationRecorders",
      "accessanalyzer:ValidatePolicy"
    ]
    resources = ["*"]
  }

  statement {
    sid = "Simulations"
    actions = [
      "iam:CreateUser",
      "iam:DeleteUser",
      "iam:PutUserPolicy",
      "iam:DeleteUserPolicy",
      "iam:AttachUserPolicy",
      "iam:DetachUserPolicy",
      "iam:ListUserPolicies",
      "iam:ListAttachedUserPolicies",
      "iam:ListAccessKeys",
      "iam:DeleteAccessKey",
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutBucketTagging",
      "s3:DeleteBucketTagging",
      "s3:PutBucketAcl",
      "s3:ListBucket",
      "s3:DeleteObject",
      "s3:ListBucketVersions",
      "s3:DeleteObjectVersion"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "task_inline" {
  name   = "${local.name}-task-inline"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task_policy.json
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode(
    [
      {
        name      = "api"
        image     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
        essential = true
        portMappings = [
          { containerPort = 8000, hostPort = 8000, protocol = "tcp" }
        ]
        environment = [
          { name = "AWS_REGION", value = var.aws_region },
          { name = "STORAGE_MODE", value = "aws" },
          { name = "ARTIFACT_BUCKET", value = aws_s3_bucket.artifacts.bucket },
          { name = "SCANS_TABLE", value = aws_dynamodb_table.scans.name },
          { name = "CORS_ORIGINS", value = "*" },
          { name = "ENV", value = "dev" },
          { name = "OWNER_TAG", value = var.owner }
        ]
        logConfiguration = {
          logDriver = "awslogs"
          options = {
            awslogs-group         = aws_cloudwatch_log_group.api.name
            awslogs-region        = var.aws_region
            awslogs-stream-prefix = "ecs"
          }
        }
      }
    ]
  )

  tags = local.tags
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api-svc"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = true
  }

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  tags = local.tags
}

# --- Web (S3 static website for dev) ---
resource "aws_s3_bucket" "web" {
  bucket = "${local.name}-web"
  force_destroy = true
  tags   = local.tags
}

resource "aws_s3_bucket_website_configuration" "web" {
  bucket = aws_s3_bucket.web.id
  index_document { suffix = "index.html" }
  error_document { key = "index.html" }
}

resource "aws_s3_bucket_public_access_block" "web" {
  bucket                  = aws_s3_bucket.web.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

data "aws_iam_policy_document" "web_public_read" {
  statement {
    sid     = "PublicRead"
    actions = ["s3:GetObject"]
    resources = [
      "${aws_s3_bucket.web.arn}/*"
    ]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "web" {
  bucket = aws_s3_bucket.web.id
  policy = data.aws_iam_policy_document.web_public_read.json
  depends_on = [
    aws_s3_bucket_public_access_block.web
  ]
}

# --- Billing alarm (must be in us-east-1) ---
provider "aws" {
  alias  = "billing"
  region = "us-east-1"
}

resource "aws_sns_topic" "billing" {
  provider = aws.billing
  name     = "${local.name}-billing"
  tags     = local.tags
}

resource "aws_sns_topic_subscription" "billing_email" {
  provider  = aws.billing
  count     = var.billing_alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.billing.arn
  protocol  = "email"
  endpoint  = var.billing_alarm_email
}

resource "aws_cloudwatch_metric_alarm" "billing" {
  provider            = aws.billing
  alarm_name          = "${local.name}-billing-USD"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600
  statistic           = "Maximum"
  threshold           = var.billing_alarm_threshold_usd
  dimensions = {
    Currency = "USD"
  }
  treat_missing_data = "notBreaching"
  alarm_actions      = [aws_sns_topic.billing.arn]
  tags               = local.tags
}
