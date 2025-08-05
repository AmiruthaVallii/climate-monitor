"""Lambda handler to extract and insert weather reading into the RDS."""
import os
from time import sleep
from typing import Any
import logging
import json
from dotenv import load_dotenv
import psycopg2
import boto3

LAMBDA_NAME = "c18-climate-monitor-new-location-orchestrator-lambda"

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO)

load_dotenv()


def get_connection() -> psycopg2.extensions.connection:
    """Get connection to RDS."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )


def get_locations() -> list:
    """Get locations from RDS."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT location_id, latitude, longitude FROM locations")
            locations = cur.fetchall()
        return locations
    finally:
        conn.close()


if __name__ == "__main__":
    locations = get_locations()
    boto3.setup_default_session(
        aws_access_key_id=os.getenv("MY_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("MY_AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("MY_AWS_REGION")
    )
    lambda_client = boto3.client('lambda')
    for location in locations:
        payload = {
            "location_id": location[0],
            "latitude": location[1],
            "longitude": location[2]
        }
        logging.info("Invoking with payload: %s", str(payload))
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        logging.info("Status code: %s",
                     response['ResponseMetadata']['HTTPStatusCode'])
        sleep(20*60)  # Respect API limit
