variable "aws_region" {
  type        = string
  description = "Deployment region"
  default     = "us-east-1"
}

variable "name_prefix" {
  type        = string
  description = "Base name prefix"
  default     = "cloudsentinel-dev"
}

variable "owner" {
  type        = string
  description = "Owner tag"
  default     = "dhyey"
}

variable "api_ingress_cidr" {
  type        = string
  description = "CIDR allowed to hit the API port (dev demo)."
  default     = "0.0.0.0/0"
}

variable "image_tag" {
  type        = string
  description = "ECR image tag to deploy"
  default     = "latest"
}

variable "desired_count" {
  type        = number
  description = "ECS service desired count (default 0 for cost control)."
  default     = 0
}

variable "billing_alarm_threshold_usd" {
  type        = number
  description = "Billing alarm threshold in USD (us-east-1)."
  default     = 10
}

variable "billing_alarm_email" {
  type        = string
  description = "Optional email address for billing alarm notifications."
  default     = ""
}

