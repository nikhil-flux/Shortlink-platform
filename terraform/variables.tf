variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "repository_name" {
  type    = string
  default = "shortlink-platform"
}

variable "github_repo" {
  description = "GitHub repo allowed to push images, as owner/name"
  type        = string
  default     = "nikhil-flux/Shortlink-platform"
}
