# pylint: skip-file
from datetime import date

from extract_future import extract_future_data

MOCK_RESPONSE = {
    'daily': {
        'time': ["2025-08-01", "2025-08-02"],
        'temperature_2m_mean': [22.5, 23.1],
        'temperature_2m_max': [28.0, 29.2],
        'temperature_2m_min': [17.5, 18.2],
        'rain_sum': [1.2, 0.0],
        'snowfall_sum': [0.0, 0.0],
        'wind_speed_10m_mean': [5.2, 4.8],
        'wind_speed_10m_max': [12.5, 11.0],
    }
}
BAD_MOCK = {
    'daily': {
        'time': ["bad-date", "2025-08-02"],
        'temperature_2m_mean': [22.5, 23.1],
        'temperature_2m_max': [28.0, 29.2],
        'temperature_2m_min': [17.5, 18.2],
        'rain_sum': [1.2, 0.0],
        'snowfall_sum': [0.0, 0.0],
        'wind_speed_10m_mean': [5.2, 4.8],
        'wind_speed_10m_max': [12.5, 11.0],
    }
}
MOCK_ENDPOINT = f'https://climate-api.open-meteo.com/v1/climate?latitude=10.0&longitude=20.0&start_date=2025-08-01&end_date=2025-08-02&models=EC_Earth3P_HR&daily=temperature_2m_max,temperature_2m_mean,temperature_2m_min,wind_speed_10m_mean,wind_speed_10m_max,rain_sum,snowfall_sum'


def test_extract_valid_data(requests_mock):

    requests_mock.get(MOCK_ENDPOINT,
                      json=MOCK_RESPONSE)
    result = extract_future_data(
        location_id=1, lat=10.0, lon=20.0, start="2025-08-01", end="2025-08-02")

    assert len(result) == 2
    assert result[0] == (
        date(2025, 8, 1), 1, 22.5, 28.0, 17.5, 1.2, 0.0, 5.2, 12.5
    )


def test_extract_with_invalid_numbers(requests_mock):

    bad_data = dict(MOCK_RESPONSE)
    bad_data["daily"]["temperature_2m_mean"] = [22.5, "bad"]
    print(bad_data)
    requests_mock.get(MOCK_ENDPOINT,
                      json=bad_data)

    result = extract_future_data(
        location_id=1, lat=10.0, lon=20.0, start="2025-08-01", end="2025-08-02")
    assert len(result) == 1
    assert result[0][0] == date(2025, 8, 1)


def test_extract_with_bad_date(requests_mock):

    requests_mock.get(MOCK_ENDPOINT,
                      json=BAD_MOCK)

    result = extract_future_data(
        location_id=1, lat=10.0, lon=20.0, start="2025-08-01", end="2025-08-02")
    assert len(result) == 1
    assert result[0][0] == date(2025, 8, 2)
