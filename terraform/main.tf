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
  allocated_storage      = 100
  db_name                = "postgres"
  identifier             = "c18-climate-monitor-rds"
  engine                 = "postgres"
  engine_version         = "17.5"
  instance_class         = "db.t3.micro"
  username               = "climate"
  password               = var.db_password
  skip_final_snapshot    = true
  publicly_accessible    = true
  vpc_security_group_ids = [aws_security_group.allow_5432.id]
  db_subnet_group_name   = "c18-public-subnet-group"
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
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Effect" : "Allow"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_exec_role" {
  role = aws_iam_role.lambda.name
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
      api_key     = var.open_weather_api_key
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
  memory_size   = 3008
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
      api_key     = var.open_weather_api_key
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

resource "aws_cloudwatch_log_group" "live_flood_warnings" {
  name              = "/aws/lambda/${var.live_flood_warnings_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.live_flood_warnings_lambda_name
  }
}

resource "aws_lambda_function" "live_flood_warnings" {
  function_name = var.live_flood_warnings_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.flood_warning_check.repository_url}:latest"
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  environment {
    variables = {
      DB_HOST     = aws_db_instance.climate.address
      DB_PORT     = 5432
      DB_USERNAME = "climate"
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
    aws_cloudwatch_log_group.live_flood_warnings
  ]
}

resource "aws_cloudwatch_log_group" "location_assignment" {
  name              = "/aws/lambda/${var.location_assignment_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.location_assignment_lambda_name
  }
}

resource "aws_lambda_function" "location_assignment" {
  function_name = var.location_assignment_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.location_assignment.repository_url}:latest"
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  environment {
    variables = {
      HOST       = aws_db_instance.climate.address
      PORT       = 5432
      USER       = "climate"
      DBPASSWORD = var.db_password
      DBNAME     = "postgres"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.location_assignment
  ]
}

resource "aws_cloudwatch_log_group" "future_climate" {
  name              = "/aws/lambda/${var.future_climate_data_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.future_climate_data_lambda_name
  }
}

resource "aws_lambda_function" "future_climate" {
  function_name = var.future_climate_data_lambda_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.future_predictions.repository_url}:latest"
  memory_size   = 3008
  timeout       = 400
  architectures = ["x86_64"]

  environment {
    variables = {
      HOST       = aws_db_instance.climate.address
      PORT       = 5432
      USER       = "climate"
      DBPASSWORD = var.db_password
      DBNAME     = "postgres"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_exec_role,
    aws_cloudwatch_log_group.future_climate
  ]
}




resource "aws_iam_role" "orchestrator_lambda" {
  name = "c18-climate-monitor-orchestrator-lambda-iam"
  assume_role_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "lambda.amazonaws.com"
        },
        "Effect" : "Allow"
      }
    ]
  })
}

resource "aws_iam_role_policy" "invoke_lambdas" {
  name = "invoke-other-lambdas"
  role = aws_iam_role.orchestrator_lambda.id

  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : "lambda:InvokeFunction",
        "Resource" : ["*"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "orchestrator_lambda_basic_exec_role" {
  role       = aws_iam_role.orchestrator_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}



resource "aws_cloudwatch_log_group" "current_reading_orchestrator" {
  name              = "/aws/lambda/${var.current_reading_orchestrator_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.current_reading_orchestrator_lambda_name
  }
}

resource "aws_lambda_function" "current_reading_orchestrator" {
  function_name = var.current_reading_orchestrator_lambda_name
  role          = aws_iam_role.orchestrator_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.current_reading_orchestrator.repository_url}:latest"
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
    aws_iam_role_policy_attachment.orchestrator_lambda_basic_exec_role,
    aws_cloudwatch_log_group.current_reading_orchestrator
  ]
}




resource "aws_cloudwatch_log_group" "new_location_orchestrator" {
  name              = "/aws/lambda/${var.new_location_orchestrator_lambda_name}"
  retention_in_days = 7

  tags = {
    Environment = "production"
    Function    = var.new_location_orchestrator_lambda_name
  }
}

resource "aws_lambda_function" "new_location_orchestrator" {
  function_name = var.new_location_orchestrator_lambda_name
  role          = aws_iam_role.orchestrator_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.new_location_orchestrator.repository_url}:latest"
  memory_size   = 256
  timeout       = 60
  architectures = ["x86_64"]

  environment {
    variables = {
      MY_AWS_ACCESS_KEY_ID     = var.my_aws_access_key_id
      MY_AWS_SECRET_ACCESS_KEY = var.my_aws_secret_access_key
      MY_AWS_REGION            = "eu-west-2"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "INFO"
  }

  depends_on = [
    aws_iam_role_policy_attachment.orchestrator_lambda_basic_exec_role,
    aws_cloudwatch_log_group.new_location_orchestrator
  ]
}



resource "aws_iam_role" "lambda_scheduler" {
  name = "c18-climate-monitor-scheduler-iam"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["scheduler.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "pipeline_scheduler" {
  name = "c18-climate-monitor-scheduler-policy"
  role = aws_iam_role.lambda_scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "*"
        ]
      }
    ]
  })
}

resource "aws_scheduler_schedule" "live_flood_warnings_scheduler" {
  name = "c18-climate-monitor-live-flood-warnings-scheduler"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(*/15 * * * ? *)"
  schedule_expression_timezone = "Europe/London"

  target {
    arn      = aws_lambda_function.live_flood_warnings.arn
    role_arn = aws_iam_role.lambda_scheduler.arn
  }
}


resource "aws_scheduler_schedule" "current_reading_orchestrator_scheduler" {
  name = "c18-climate-monitor-current_reading_orchestrator-scheduler"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(*/15 * * * ? *)"
  schedule_expression_timezone = "Europe/London"

  target {
    arn      = aws_lambda_function.current_reading_orchestrator.arn
    role_arn = aws_iam_role.lambda_scheduler.arn
  }
}


# ECS Task Execution Role

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c18-climate-monitor-ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# Security Group


resource "aws_security_group" "streamlit_sg" {
  name        = "c18-climate-monitor-streamlit-sg"
  description = "Allow inbound traffic to Streamlit dashboard"
  vpc_id      = "vpc-0adcb6a62ca552c01"

  ingress {
    description = "Allow traffic on port 8501"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "climate-monitor-dashboard-sg"
  }
}


# ECS Cluster

data "aws_ecs_cluster" "existing" {
  cluster_name = "c18-ecs-cluster"
}

# Cloudwatch

resource "aws_cloudwatch_log_group" "streamlit_logs" {
  name              = "/ecs/c18-climate-monitor-dashboard"
  retention_in_days = 7
}



# ECS Task Definition

resource "aws_ecs_task_definition" "streamlit_dashboard" {
  family                   = "streamlit-dashboard-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "streamlit"
      image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c18-week-13-team-1-project-ecr@sha256:bc3471fbf81c0bcad6612d3abc88f456d91df3435bdaf5af7e9e99bf41ba43dd"
      essential = true
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ],
      environment = [
        { name = "DB_SERVER", value = var.db_server },
        { name = "DB_NAME", value = var.db_name },
        { name = "DB_USERNAME", value = var.db_username },
        { name = "DB_PASSWORD", value = var.db_password }
      ],
      logConfiguration = {
      logDriver = "awslogs",
      options = {
        awslogs-group         = "/ecs/c18-climate-monitor-dashboard"
        awslogs-region        = "eu-west-2"
        awslogs-stream-prefix = "c18-climate-monitor"
      }
    }
    }
  ])
}

# ECS Fargate Service

resource "aws_ecs_service" "streamlit_service" {
  name            = "c18-climate-monitor-dashboard-service"
  cluster         = data.aws_ecs_cluster.existing.id
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.streamlit_dashboard.arn
  desired_count   = 1

  network_configuration {
    subnets         = ["subnet-0679d4b1f9e7839ef", "subnet-0f10662561eade8c3", "subnet-0aed07ac008a10da9"]
    security_groups = [aws_security_group.streamlit_sg.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_iam_role_policy_attachment.ecs_execution_policy
  ]
}