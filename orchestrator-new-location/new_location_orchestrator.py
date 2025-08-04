"""Load data trigger lambdas to load data for new locations."""
from datetime import date, timedelta
from typing import Any
import json
import logging
import boto3
# from dotenv import load_dotenv

HISTORIC_WEATHER_FIRST_DATE = date.fromisoformat(
    '2010-12-01')  # date.fromisoformat('1940-01-01')
HISTORIC_WEATHER_LAST_DATE = date.fromisoformat(
    '2011-02-24')  # date.today() - timedelta(days=6)
HISTORIC_WEATHER_BATCH_SIZE = 7
FUTURE_PREDICTIONS_FIRST_DATE = date.fromisoformat(
    '2026-05-04')  # date.today() + timedelta(days=1)
FUTURE_PREDICTIONS_LAST_DATE = date.fromisoformat(
    '2026-08-12')  # date.fromisoformat('2049-12-31')
FUTURE_PREDICTIONS_BATCH_SIZE = 100
HISTORIC_WEATHER_LAMBDA = "c18-climate-monitor-historic-weather-lambda"
HISTORIC_AIR_QUALITY_LAMBDA = "c18-climate-monitor-historic-air-quality-lambda"
FUTURE_PREDICTIONS_LAMBDA = "c18-climate-monitor-future-predictions-lambda"
LOCATION_ASSIGNMENT_LAMBDA = "c18-climate-monitor-location-assignment-lambda"

# load_dotenv()

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO)


def invoke_with_date_range(lambda_name: str,
                           location: dict,
                           start: date,
                           end: date,
                           client: Any) -> None:
    """Invoke `lambda_name` for location between start and end date."""
    payload = {
        "start_date": start.isoformat(),
        "end_date": end.isoformat()
    }
    logging.info("Invoking %s with date range: %s", lambda_name, str(payload))
    payload = payload | location
    response = client.invoke(
        FunctionName=lambda_name,
        InvocationType="Event",
        Payload=json.dumps(payload)
    )
    logging.info("Status code: %s",
                 response['ResponseMetadata']['HTTPStatusCode'])


# def insert_historic_weather(location: dict, client: Any) -> None:
#     """Invoke lambdas to insert all historic weather data for the location."""
#     start_date = HISTORICAL_WEATHER_FIRST_DATE
#     end_date = HISTORICAL_WEATHER_FIRST_DATE + \
#         timedelta(days=BATCH_SIZE - 1)
#     while end_date < HISTORICAL_WEATHER_LAST_DATE:
#         invoke_with_date_range(HISTORIC_WEATHER_LAMBDA,
#                                location, start_date, end_date, client)
#         start_date += timedelta(days=BATCH_SIZE)
#         end_date += timedelta(days=BATCH_SIZE)
#     invoke_with_date_range(HISTORIC_WEATHER_LAMBDA,
#                            location, start_date,
#                            HISTORICAL_WEATHER_LAST_DATE, client)


def date_batch_invoke(lambda_name: str,
                      location: dict,
                      first_date: date,
                      last_date: date,
                      batch_size: int,
                      client: Any) -> None:
    """
    Invoke `lambda_name` to cover the range from `first_date` to `last_date`.
    Parameters:
        lambda_name: Name of the lambda function to invoke.
        location: Dict containing the location_id, latitude and longitude.
            e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758}
        first_date: First date in the desired range.
        last_date: Last date in the desired range.
        batch_size: Number of days in a batch.
        client: boto3 Lambda client
    Returns:
        None
    """
    start_date = first_date
    end_date = first_date + timedelta(days=batch_size - 1)
    while end_date < last_date:
        invoke_with_date_range(lambda_name, location,
                               start_date, end_date, client)
        start_date += timedelta(days=batch_size)
        end_date += timedelta(days=batch_size)
    invoke_with_date_range(lambda_name, location,
                           start_date, last_date, client)


def invoke(lambda_name: str, payload: dict, client: Any) -> None:
    """Invoke `lambda_name` with `payload`."""
    response = client.invoke(
        FunctionName=lambda_name,
        InvocationType="Event",
        Payload=json.dumps(payload)
    )
    logging.info("Invoked %s. Status code: %s",
                 lambda_name,
                 response['ResponseMetadata']['HTTPStatusCode'])


def lambda_handler(event: dict, context: Any) -> dict:  # pylint: disable=unused-argument
    """
    Orchestrates lambdas to load data for a new location.
    Parameters:
        event: Dict containing the location_id, latitude and longitude.
            e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    lambda_client = boto3.client('lambda')
    try:
        date_batch_invoke(HISTORIC_WEATHER_LAMBDA, event, HISTORIC_WEATHER_FIRST_DATE,
                          HISTORIC_WEATHER_LAST_DATE, HISTORIC_WEATHER_BATCH_SIZE, lambda_client)
        date_batch_invoke(FUTURE_PREDICTIONS_LAMBDA, event, FUTURE_PREDICTIONS_FIRST_DATE,
                          FUTURE_PREDICTIONS_LAST_DATE, FUTURE_PREDICTIONS_BATCH_SIZE, lambda_client)
        invoke(HISTORIC_AIR_QUALITY_LAMBDA, event, lambda_client)
        invoke(LOCATION_ASSIGNMENT_LAMBDA, event, lambda_client)

        return {
            "statusCode": 200,
            "message": "Successfully invoked all lambdas."
        }
    except Exception as e:
        logging.error("Error for location_id %s: %s",
                      event["location_id"], str(e))
        raise e


if __name__ == "__main__":
    lambda_handler(
        {"location_id": 23, "latitude": 50.2632, "longitude": -5.051},
        "context")
