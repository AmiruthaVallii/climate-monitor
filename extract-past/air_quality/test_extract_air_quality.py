import os
from datetime import datetime
import pytest
from dotenv import load_dotenv

from extract_air_quality import HISTORIC_DATA_START_DATE, get_air_quality

load_dotenv()


@pytest.fixture
def api_response():
    return {
        "coord": {
            "lon": -0.1278,
            "lat": 51.5074
        },
        "list": [
            {
                "main": {
                    "aqi": 2
                },
                "components": {
                    "co": 347.14,
                    "no": 33.53,
                    "no2": 41.13,
                    "o3": 0.01,
                    "so2": 7.51,
                    "pm2_5": 18.81,
                    "pm10": 21.35,
                    "nh3": 0.25
                },
                "dt": 1606435200
            },
            {
                "main": {
                    "aqi": 2
                },
                "components": {
                    "co": 293.73,
                    "no": 11.18,
                    "no2": 42.16,
                    "o3": 0.21,
                    "so2": 7.27,
                    "pm2_5": 15.68,
                    "pm10": 18.17,
                    "nh3": 0.01
                },
                "dt": 1606438800
            }
        ]
    }


@pytest.fixture
def api_error():
    return {
        "cod": 401,
        "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
    }


def test_returns_valid_data_from_api(requests_mock, api_response):
    mock = requests_mock.get(
        f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat=51.507351&lon=-0.127758&start={HISTORIC_DATA_START_DATE}&end={int(datetime.now().timestamp())}&appid={os.getenv("api_key")}", json=api_response, status_code=200)
    mocked_response = get_air_quality(1, 51.507351, -0.127758)
    assert mock.call_count == 1
    assert mocked_response == [
        (datetime(2020, 11, 27, 0, 0), 1, 2, 347.14, 41.13,
         33.53, 0.25, 0.01, 7.51, 18.81, 21.35),
        (datetime(2020, 11, 27, 1, 0), 1, 2, 293.73, 42.16,
         11.18, 0.01, 0.21, 7.27, 15.68, 18.17)
    ]


def test_invalid_api_key_raises_error(requests_mock, api_error):
    mock = requests_mock.get(
        f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat=51.507351&lon=-0.127758&start={HISTORIC_DATA_START_DATE}&end={int(datetime.now().timestamp())}&appid={os.getenv("api_key")}", json=api_error, status_code=401)
    with pytest.raises(RuntimeError) as err:
        get_air_quality(1, 51.507351, -0.127758)
    assert mock.call_count == 1
    assert str(err.value) == "Error reaching the API for location ID 1. Error code: 401. Message: Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
