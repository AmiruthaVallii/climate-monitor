"""Lambda handler to extract and insert readings into the RDS."""
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
                    "wind_gusts_10m", "rain"],
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
    data["timestamp"] = datetime.fromtimestamp(
        current_weather.Time(), timezone.utc).isoformat()
    return data


def get_air_quality(latitude: float, longitude: float) -> dict:
    """Get air quality data from openweathermap.org."""
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    retry_session = retry(req.Session(), retries=5, backoff_factor=0.2)
    r = retry_session.get(
        url + f"?lat={latitude}&lon={longitude}&appid={os.getenv("api_key")}")
    raw_data = r.json()["list"][0]
    processed_data = {}
    processed_data["timestamp"] = datetime.fromtimestamp(
        raw_data['dt'], timezone.utc).isoformat()
    processed_data["air_quality_index"] = raw_data['main']['aqi']
    processed_data["carbon_monoxide"] = raw_data['components']["co"]
    processed_data["nitrogen_dioxide"] = raw_data['components']["no2"]
    processed_data["ozone"] = raw_data['components']["o3"]
    processed_data["sulphur_dioxide"] = raw_data['components']["so2"]
    processed_data["pm2_5"] = raw_data['components']["pm2_5"]
    processed_data["pm10"] = raw_data['components']["pm10"]
    processed_data["nitrogen_monoxide"] = raw_data['components']["no"]
    processed_data["ammonia"] = raw_data['components']["nh3"]
    return processed_data


def lambda_handler(event: dict, context: Any) -> dict:  # pylint: disable=unused-argument
    """
    Uploads current weather data for given location_id
    Parameters:
        event: Dict containing the location_id e.g. {"location_id": 1}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT latitude, longitude FROM locations WHERE location_id = %s",
                (event["location_id"],))
            lat, lon = cur.fetchone()
        weather_reading = get_weather(lat, lon)
        weather_reading["location_id"] = event["location_id"]
        with conn.cursor() as cur:
            cur.execute(
                ("INSERT INTO weather_readings "
                 "(timestamp, location_id, rainfall_last_15_mins, "
                 "current_temperature, wind_speed, "
                 "wind_gust_speed, wind_direction) "
                 "VALUES "
                 "(%(timestamp)s, %(location_id)s, %(rainfall_last_15_mins)s, "
                 "%(current_temperature)s, %(wind_speed)s, "
                 "%(wind_gust_speed)s, %(wind_direction)s)"),
                weather_reading)
            conn.commit()
        air_quality_reading = get_air_quality(lat, lon)
        air_quality_reading["location_id"] = event["location_id"]
        with conn.cursor() as cur:
            cur.execute(
                ("INSERT INTO air_quality_readings "
                 "(timestamp, location_id, air_quality_index,"
                 "carbon_monoxide, nitrogen_monoxide, ammonia, "
                 "nitrogen_dioxide, ozone, sulphur_dioxide, "
                 "pm2_5, pm10) "
                 "VALUES "
                 "(%(timestamp)s, %(location_id)s, %(air_quality_index)s,"
                 "%(carbon_monoxide)s, %(nitrogen_monoxide)s, %(ammonia)s, "
                 "%(nitrogen_dioxide)s, %(ozone)s, %(sulphur_dioxide)s, "
                 "%(pm2_5)s, %(pm10)s)"),
                air_quality_reading
            )
            conn.commit()
    finally:
        conn.close()
    return {
        "statusCode": 200,
        "message": "Reading successfully inserted."
    }


if __name__ == "__main__":
    out = lambda_handler({"location_id": 1}, 1)
    print(out)
