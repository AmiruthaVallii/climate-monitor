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

resource "aws_ecr_repository" "location_assignment" {
  name                 = "c18-climate-monitor-location-assignment-ecr"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_iam_policy_document" "example" {
  statement {
    sid    = "LambdaECRImageRetrievalPolicy"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage"
    ]
  }
}

resource "aws_ecr_repository_policy" "example" {
  repository = aws_ecr_repository.historic_air_quality.name
  policy     = data.aws_iam_policy_document.example.json
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

resource "aws_iam_role" "lambda" {
  name = "c18-climate-monitor-lambda-iam"
  assume_role_policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_exec_role" {
  role       = aws_iam_role.lambda.name
  # Provides write permissions to CloudWatch Logs
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "current_weather" {
  name              = "/aws/lambda/${var.current_weather_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.current_weather_lambda_name
  }
}

resource "aws_lambda_function" "current_weather" {
  function_name = var.current_weather_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.current_weather.repository_url}:latest"
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  environment {
    variables = {
      DB_HOST     = aws_db_instance.climate.address
      DB_PORT     = 5432
      DB_USER     = "climate"
      DB_PASSWORD = var.db_password
      DB_NAME     = "postgres"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.current_weather
  ]
}

resource "aws_cloudwatch_log_group" "current_air_quality" {
  name              = "/aws/lambda/${var.current_air_quality_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.current_air_quality_lambda_name
  }
}

resource "aws_lambda_function" "current_air_quality" {
  function_name = var.current_air_quality_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.current_air_quality.repository_url}:latest"
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  environment {
    variables = {
      DB_HOST     = aws_db_instance.climate.address
      DB_PORT     = 5432
      DB_USER     = "climate"
      DB_PASSWORD = var.db_password
      DB_NAME     = "postgres"
      api_key = var.open_weather_api_key
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.current_air_quality
  ]
}

resource "aws_cloudwatch_log_group" "historic_weather" {
  name              = "/aws/lambda/${var.historic_weather_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.historic_weather_lambda_name
  }
}

resource "aws_lambda_function" "historic_weather" {
  function_name = var.historic_weather_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.historic_weather.repository_url}:latest"
  memory_size   = 512
  timeout       = 400
  architectures = ["x86_64"]

  environment {
    variables = {
      DB_HOST     = aws_db_instance.climate.address
      DB_PORT     = 5432
      DB_USER     = "climate"
      DB_PASSWORD = var.db_password
      DB_NAME     = "postgres"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.historic_weather
  ]
}

resource "aws_cloudwatch_log_group" "historic_air_quality" {
  name              = "/aws/lambda/${var.historic_air_quality_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.historic_air_quality_lambda_name
  }
}

resource "aws_lambda_function" "historic_air_quality" {
  function_name = var.historic_air_quality_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.historic_air_quality.repository_url}:latest"
  memory_size   = 1024
  timeout       = 400
  architectures = ["x86_64"]

  environment {
    variables = {
      DB_HOST     = aws_db_instance.climate.address
      DB_PORT     = 5432
      DB_USER     = "climate"
      DB_PASSWORD = var.db_password
      DB_NAME     = "postgres"
      api_key = var.open_weather_api_key
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.historic_air_quality
  ]
}
