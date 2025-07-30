output "rds_public_address" {
    value = aws_db_instance.climate.address
    description = "Public address/host of the RDS instance"
}