variable "db_password" {
  type      = string
  sensitive = true
}

variable "open_weather_api_key" {
  type      = string
  sensitive = true
}

variable "current_weather_lambda_name" {
  type    = string
  default = "c18-climate-monitor-current-weather-lambda"
}

variable "current_air_quality_lambda_name" {
  type    = string
  default = "c18-climate-monitor-current-air-quality-lambda"
}

variable "historic_weather_lambda_name" {
  type    = string
  default = "c18-climate-monitor-historic-weather-lambda"
}

variable "historic_air_quality_lambda_name" {
  type    = string
  default = "c18-climate-monitor-historic-air-quality-lambda"
}

variable "live_flood_warnings_lambda_name" {
  type    = string
  default = "c18-climate-monitor-live-flood-warnings-lambda"
}
variable "future_climate_data_lambda_name" {
  type    = string
  default = "c18-climate-monitor-future-predictions-lambda"
}
variable "location_assignment_lambda_name" {
  type    = string
  default = "c18-climate-monitor-location-assignment-lambda"
}

variable "current_reading_orchestrator_lambda_name" {
  type    = string
  default = "c18-climate-monitor-current-reading-orchestrator-lambda"
}

variable "new_location_orchestrator_lambda_name" {
  type    = string
  default = "c18-climate-monitor-new-location-orchestrator-lambda"
}

variable "my_aws_access_key_id" {
  type      = string
  sensitive = true
}

variable "my_aws_secret_access_key" {
  type      = string
  sensitive = true
}