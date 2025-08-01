"""
Python script to retrieve historic air pollution data from the OpenWeather Air Pollution API.
The data is inserted into the historical_air_quality table in the RDS
"""

import os
from datetime import datetime
from typing import Any
import logging
import random

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import requests as req
from retry_requests import retry


load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

HISTORIC_DATA_START_DATE = int(datetime(2020, 11, 27, 0, 0, 0).timestamp())

API_ENDPOINT = "http://api.openweathermap.org/data/2.5/air_pollution/history"


def get_connection() -> psycopg2.extensions.connection:
    """Get connection to RDS."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )


def get_air_quality(location_id: int, lat: float, lon: float) -> list[tuple]:
    """
    Make a request to the OpenWeather API and retrieve the historic air pollution data.
    Return the data as a list of tuples.
    """
    retry_session = retry(req.Session(),
                          retries=6,
                          backoff_factor=random.uniform(1, 3))
    api_response = retry_session.get(
        API_ENDPOINT + (
            f"?lat={lat}&lon={lon}"
            f"&start={HISTORIC_DATA_START_DATE}&end={int(datetime.now().timestamp())}"
            f"&appid={os.getenv("api_key")}"
        )
    )
    if api_response.status_code != 200:
        print(api_response.content)
        raise RuntimeError(
            f"Error reaching the API for location ID {location_id}. "
            f"Error code: {api_response.status_code}. "
            f"Message: {api_response.json()["message"]}")

    aq_data = api_response.json()["list"]

    logging.info("Data retrieved from API for location ID %d", location_id)

    data_to_insert = []

    for reading in aq_data:
        row = (
            datetime.fromtimestamp(reading["dt"]),
            location_id,
            reading["main"]["aqi"],
            reading["components"]["co"],
            reading["components"]["no2"],
            reading["components"]["no"],
            reading["components"]["nh3"],
            reading["components"]["o3"],
            reading["components"]["so2"],
            reading["components"]["pm2_5"],
            reading["components"]["pm10"]
        )
        data_to_insert.append(row)

    return data_to_insert


def insert_aq_data(data_to_insert: list[tuple]) -> None:
    """Insert historical air quality data into RDS"""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            execute_values(
                cur,
                """INSERT INTO historical_air_quality (
                        timestamp,
                        location_id,
                        hourly_air_quality_index,
                        hourly_carbon_monoxide,
                        hourly_nitrogen_dioxide,
                        hourly_nitrogen_monoxide,
                        hourly_ammonia,
                        hourly_ozone,
                        hourly_sulphur_dioxide,
                        hourly_pm2_5,
                        hourly_pm10
                    ) VALUES %s
                """,
                data_to_insert)
        conn.commit()
        logging.info(
            "Data inserted into database for location ID %d", data_to_insert[0][1])
    finally:
        conn.close()


def lambda_handler(event: dict, context: Any = None):  # pylint: disable=unused-argument
    """
    Run the functions to retrieve the data and insert it into the RDS
    Takes in an event dictionary with an ID, lat, and lon 
    """

    data_to_insert = get_air_quality(
        event["location_id"], event["latitude"], event["longitude"])
    insert_aq_data(data_to_insert)

    return {
        "statusCode": 200,
        "message": "Historical data successfully inserted."
    }


if __name__ == "__main__":

    lambda_handler(
        {
            "location_id": 1,
            "latitude": 51.507351,
            "longitude": -0.127758
        })
