terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }

  backend "s3" {
    bucket = "c18climatemonitortfstates3"
    region = "eu-west-2"
    key    = "terraform.tfstate"
  }
}

provider "aws" {
  region = "eu-west-2"
}

resource "aws_security_group" "allow_5432" {
  name        = "c18-climate-monitor-rds-sg"
  description = "Allows all traffic on port 5432."
  vpc_id      = "vpc-0adcb6a62ca552c01" # c18-VPC
}

resource "aws_vpc_security_group_ingress_rule" "allow_ingress_5432" {
  security_group_id = aws_security_group.allow_5432.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}

resource "aws_db_instance" "climate" {
  allocated_storage    = 100
  db_name = "postgres"
  identifier             = "c18-climate-monitor-rds"
  engine               = "postgres"
  engine_version       = "17.5"
  instance_class       = "db.t3.micro"
  username             = "climate"
  password             = var.db_password
  skip_final_snapshot  = true
  publicly_accessible = true
  vpc_security_group_ids = [aws_security_group.allow_5432.id]
  db_subnet_group_name = "c18-public-subnet-group"
}

resource "aws_ecr_repository" "current_weather" {
  name                 = "c18-climate-monitor-current-weather-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "current_air_quality" {
  name                 = "c18-climate-monitor-current-air-quality-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "historic_weather" {
  name                 = "c18-climate-monitor-historic-weather-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "future_predictions" {
  name                 = "c18-climate-monitor-future-predictions-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "historic_air_quality" {
  name                 = "c18-climate-monitor-historic-air-quality-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "new_location_orchestrator" {
  name                 = "c18-climate-monitor-new-location-orchestrator-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "current_reading_orchestrator" {
  name                 = "c18-climate-monitor-current-reading-orchestrator-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "flood_warning_check" {
  name                 = "c18-climate-monitor-flood-warning-check-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "daily_summary" {
  name                 = "c18-climate-monitor-daily-summary-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "dashboard" {
  name                 = "c18-climate-monitor-dashboard-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}