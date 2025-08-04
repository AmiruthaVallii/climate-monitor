"""
A Python script to invoke the lambdas for extracting and inserting all live data
"""
import os
import logging
from typing import Any
import json

from dotenv import load_dotenv
import boto3
import psycopg2


load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

lambda_client = boto3.client("lambda")

LIVE_WEATHER_LAMBDA = "c18-climate-monitor-current-weather-lambda"
LIVE_AIR_QUALITY_LAMBDA = "c18-climate-monitor-current-air-quality-lambda"


def get_connection() -> psycopg2.extensions.connection:
    """Get connection to RDS."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )


def get_location_data() -> list[tuple]:
    """Return all data from the location table in the RDS"""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM locations")
            location_data = cur.fetchall()
        logging.info("Location data retrieved from RDS")
    finally:
        conn.close()
    return location_data


def lambda_handler(event: Any = None, context: Any = None) -> None:  # pylint: disable=unused-argument
    """Lambda function to invoke the live weather and air quality lambdas for every location"""
    location_data = get_location_data()

    for location in location_data:

        payload = {
            "location_id": location[0],
            "latitude": location[2],
            "longitude": location[3]
        }

        # Live weather data
        weather_response = lambda_client.invoke(
            FunctionName=LIVE_WEATHER_LAMBDA,
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        logging.info("Weather data for %s uploaded - Status code: %s", location[1],
                     weather_response['ResponseMetadata']['HTTPStatusCode'])

        # Live air quality data
        aq_response = lambda_client.invoke(
            FunctionName=LIVE_AIR_QUALITY_LAMBDA,
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        logging.info("Air quality data for %s uploaded - Status code: %s", location[1],
                     aq_response['ResponseMetadata']['HTTPStatusCode'])

    logging.info("Successfully inserted all live data.")

    return {
        "statusCode": 200,
        "message": "Successfully inserted all live data."
    }


if __name__ == "__main__":
    lambda_handler()
