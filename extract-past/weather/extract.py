"""Lambda handler to extract and insert historical weather into the RDS."""
import os
import random
import logging
from typing import Any
import openmeteo_requests
import pandas as pd
from retry_requests import retry
from dotenv import load_dotenv
import requests as req
from sqlalchemy import create_engine, URL
from sqlalchemy.engine import Engine

load_dotenv()

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO)


def get_engine() -> Engine:
    """Create SQL Alchemy engine for the RDS."""
    url_object = URL.create(
        drivername="postgresql+psycopg2",
        host=os.getenv("DB_HOST"),
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )
    return create_engine(url_object)


def get_weather(latitude: float, longitude: float, start_date: str,
                end_date: str) -> pd.DataFrame:
    """Get the weather data for the specified location and date range."""
    # Setup the Open-Meteo API client with retry on error
    # Random backoff_factor prevents synchronized retries when run in parallel
    retry_session = retry(req.Session(),
                          retries=6,
                          backoff_factor=random.uniform(1, 3))
    openmeteo = openmeteo_requests.Client(session=retry_session)
    # The order of variables in hourly is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["temperature_2m", "wind_speed_10m", "wind_direction_10m",
                   "wind_gusts_10m", "rain", "snowfall"],
    }
    logging.info("Sending request to API.")
    api_responses = openmeteo.weather_api(url, params=params)
    # Process first (and only) location.
    api_response = api_responses[0]
    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = api_response.Hourly()
    hourly_data = {"timestamp": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}
    hourly_data["hourly_temperature"] = hourly.Variables(0).ValuesAsNumpy()
    hourly_data["hourly_wind_speed"] = hourly.Variables(1).ValuesAsNumpy()
    hourly_data["hourly_wind_direction"] = hourly.Variables(2).ValuesAsNumpy()
    hourly_data["hourly_wind_gust_speed"] = hourly.Variables(3).ValuesAsNumpy()
    hourly_data["hourly_rainfall"] = hourly.Variables(4).ValuesAsNumpy()
    hourly_data["hourly_snowfall"] = hourly.Variables(5).ValuesAsNumpy()

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    logging.info("API response processed successfully.")
    return hourly_dataframe


def lambda_handler(event: dict, context: Any) -> dict:  # pylint: disable=unused-argument
    """
    Uploads historical weather data for given location_id and date range.
    Parameters:
        event: Dict containing the location_id, start_date and end_date 
            e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758,
                  "start_date": "1940-01-01", "end_date": "1960-01-01"}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    try:
        weather_df = get_weather(event["latitude"], event["longitude"],
                                 event["start_date"], event["end_date"])
        weather_df["location_id"] = event["location_id"]
        engine = get_engine()
        logging.info("Connected to the database.")
        try:
            weather_df.to_sql("historical_weather_readings",
                              engine,
                              if_exists="append",
                              index=False,
                              chunksize=5000,
                              method="multi")
            logging.info("Historical weather data successfully inserted.")
        finally:
            engine.dispose()
        return {
            "statusCode": 200,
            "message": "Historical weather data successfully inserted."
        }
    except Exception as e:
        logging.error("Error processing location_id %s: %s",
                      event["location_id"],
                      str(e))
        raise e


if __name__ == "__main__":
    out = lambda_handler({"location_id": 18,
                          "latitude": 51.454514,
                          "longitude": -2.58791,
                          "start_date": "1940-01-01",
                          "end_date": "1975-01-01"},
                         "context")
    print(out)
