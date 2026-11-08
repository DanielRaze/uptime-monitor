variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "eu-central-1"
}

variable "ssh_cidr" {
  description = "Public IPv4 address allowed to connect over SSH, as a /32 CIDR."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.ssh_cidr)) && endswith(var.ssh_cidr, "/32")
    error_message = "Use a single public IPv4 address in CIDR notation, such as 203.0.113.10/32."
  }
}

variable "ssh_public_key_path" {
  description = "Path to an OpenSSH public key."
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}
