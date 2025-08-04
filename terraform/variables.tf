variable "db_password" {
  type = string
}

variable "open_weather_api_key" {
  type = string
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