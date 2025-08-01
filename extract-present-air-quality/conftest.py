# pylint: skip-file
import pytest


@pytest.fixture()
def response_payload():
    return {
        "coord": {
            "lon": 23.5,
            "lat": 76.4
        },
        "list": [
            {
                "main": {
                    "aqi": 2
                },
                "components": {
                    "co": 297.06,
                    "no": 0,
                    "no2": 0.12,
                    "o3": 89.44,
                    "so2": 0.21,
                    "pm2_5": 7.59,
                    "pm10": 12.05,
                    "nh3": 0.49
                },
                "dt": 1753987280
            }
        ]
    }


@pytest.fixture()
def expected_return():
    return {
        "air_quality_index": 2,
        "carbon_monoxide": 297.06,
        "nitrogen_monoxide": 0,
        "nitrogen_dioxide": 0.12,
        "ozone": 89.44,
        "sulphur_dioxide": 0.21,
        "pm2_5": 7.59,
        "pm10": 12.05,
        "ammonia": 0.49,
        "timestamp": '2025-07-31T18:41:20+00:00'
    }
