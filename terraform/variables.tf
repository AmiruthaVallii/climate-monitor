variable "db_password" {
    type = string
}

variable "open_weather_api_key" {
    type = string
}

variable "current_weather_lambda_name" {
  type        = string
  default     = "c18-climate-monitor-current-weather-lambda"
}

variable "current_air_quality_lambda_name" {
  type        = string
  default     = "c18-climate-monitor-current-air-quality-lambda"
}

variable "historic_weather_lambda_name" {
  type        = string
  default     = "c18-climate-monitor-historic-weather-lambda"
}

variable "historic_air_quality_lambda_name" {
  type        = string
  default     = "c18-climate-monitor-historic-air-quality-lambda"
}