"""Lambda handler to extract and insert weather reading into the RDS."""
import os
from datetime import datetime, timezone
from typing import Any
import openmeteo_requests
from retry_requests import retry
from dotenv import load_dotenv
import psycopg2
import requests as req


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


def get_weather(latitude: float, longitude: float) -> dict:
    """Get the current weather conditions from open-meteo.com"""
    session = req.Session()
    retry_session = retry(session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "wind_speed_10m", "wind_direction_10m",
                    "wind_gusts_10m", "rain", "snowfall"],
    }
    api_responses = openmeteo.weather_api(url, params=params)
    api_response = api_responses[0]
    # Process current data. The order of variables needs to be the same as requested.
    current_weather = api_response.Current()
    data = {}
    data["current_temperature"] = current_weather.Variables(0).Value()
    data["wind_speed"] = current_weather.Variables(1).Value()
    data["wind_direction"] = current_weather.Variables(2).Value()
    data["wind_gust_speed"] = current_weather.Variables(3).Value()
    data["rainfall_last_15_mins"] = current_weather.Variables(4).Value()
    data["snowfall_last_15_mins"] = current_weather.Variables(5).Value()
    data["timestamp"] = datetime.fromtimestamp(
        current_weather.Time(), timezone.utc).isoformat()
    return data


def insert_reading(reading: dict) -> None:
    """Insert reading into the RDS."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                ("INSERT INTO weather_readings "
                 "(timestamp, location_id, rainfall_last_15_mins, "
                 "current_temperature, wind_speed, "
                 "wind_gust_speed, wind_direction, "
                 "snowfall_last_15_mins) "
                 "VALUES "
                 "(%(timestamp)s, %(location_id)s, %(rainfall_last_15_mins)s, "
                 "%(current_temperature)s, %(wind_speed)s, "
                 "%(wind_gust_speed)s, %(wind_direction)s, "
                 "%(snowfall_last_15_mins)s)"),
                reading)
            conn.commit()
    finally:
        conn.close()


def lambda_handler(event: dict, context: Any) -> dict:  # pylint: disable=unused-argument
    """
    Uploads current weather data for given location_id
    Parameters:
        event: Dict containing the location_id 
               e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        weather_reading = get_weather(event["latitude"], event["longitude"])
        weather_reading["location_id"] = event["location_id"]
        insert_reading(weather_reading)
    except Exception as e:
        return {
            "statusCode": 500,
            "message": str(e)
        }
    return {
        "statusCode": 200,
        "message": "Reading successfully inserted."
    }


if __name__ == "__main__":
    out = lambda_handler(
        {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758},
        "context"
    )
    print(out)
