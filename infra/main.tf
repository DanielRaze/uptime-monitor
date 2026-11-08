terraform {
  required_version = ">= 1.10, < 2.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project = "uptime-monitor"
    }
  }
}

resource "aws_vpc" "monitor" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "monitor" {
  vpc_id     = aws_vpc.monitor.id
  cidr_block = "10.42.1.0/24"
}

resource "aws_internet_gateway" "monitor" {
  vpc_id = aws_vpc.monitor.id
}

resource "aws_route_table" "monitor" {
  vpc_id = aws_vpc.monitor.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.monitor.id
  }
}

resource "aws_route_table_association" "monitor" {
  subnet_id      = aws_subnet.monitor.id
  route_table_id = aws_route_table.monitor.id
}

resource "aws_security_group" "monitor" {
  name_prefix = "uptime-monitor-"
  description = "SSH access for Uptime Monitor"
  vpc_id      = aws_vpc.monitor.id
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.monitor.id
  cidr_ipv4         = var.ssh_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "internet" {
  security_group_id = aws_security_group.monitor.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_key_pair" "monitor" {
  key_name_prefix = "uptime-monitor-"
  public_key      = trimspace(file(pathexpand(var.ssh_public_key_path)))
}

data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/noble/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_instance" "monitor" {
  ami                         = data.aws_ssm_parameter.ubuntu_ami.insecure_value
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.monitor.id
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.monitor.id]
  key_name                    = aws_key_pair.monitor.key_name
  user_data                   = file("${path.module}/bootstrap.sh")
  user_data_replace_on_change = true

  credit_specification {
    cpu_credits = "standard"
  }

  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 16
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = "uptime-monitor"
  }

  depends_on = [
    aws_route_table_association.monitor,
    aws_vpc_security_group_egress_rule.internet,
  ]
}

output "public_ip" {
  description = "Public IPv4 address of the EC2 instance."
  value       = aws_instance.monitor.public_ip
}
