variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "jenkins-ecr-demo"
}

variable "my_ip_cidr" {
  type        = string
  description = "Your public IPv4 address with /32, for example 203.0.113.10/32."

  validation {
    condition     = can(cidrnetmask(var.my_ip_cidr))
    error_message = "Provide a valid IPv4 CIDR, preferably your-ip/32."
  }
}

variable "jenkins_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "app_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "app_http_cidr" {
  type    = string
  default = "0.0.0.0/0"
}

variable "enable_ssh" {
  type    = bool
  default = false
}

variable "key_pair_name" {
  type    = string
  default = ""
}
