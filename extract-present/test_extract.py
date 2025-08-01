from unittest.mock import patch, Mock, call
from extract import get_weather, lambda_handler


@patch("openmeteo_requests.Client")
def test_get_weather(api_mock):
    current_weather_mock = Mock()
    response_mock = Mock()
    openmeteo = Mock()
    response_mock.Current.return_value = current_weather_mock
    current_weather_mock.Time.return_value = 1753964100
    current_weather_mock.Variables.return_value.Value.side_effect = [
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0
    ]
    api_mock.return_value = openmeteo
    openmeteo.weather_api.return_value = [response_mock]
    ret = get_weather(53.5, 0.1)
    openmeteo.weather_api.assert_called_once_with(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": 53.5,
            "longitude": 0.1,
            "current": ["temperature_2m", "wind_speed_10m", "wind_direction_10m",
                        "wind_gusts_10m", "rain", "snowfall"]
        }
    )
    assert ret == {
        'current_temperature': 0.0,
        'wind_speed': 1.0,
        'wind_direction': 2.0,
        'wind_gust_speed': 3.0,
        'rainfall_last_15_mins': 4.0,
        'snowfall_last_15_mins': 5.0,
        'timestamp': '2025-07-31T12:15:00+00:00'
    }


@patch("extract.get_weather")
@patch("psycopg2.connect")
def test_lambda_handler(mock_connect, mock_get_weather):
    cursor = Mock()
    weather_reading = {
        'current_temperature': 0.0,
        'wind_speed': 1.0,
        'wind_direction': 2.0,
        'wind_gust_speed': 3.0,
        'rainfall_last_15_mins': 4.0,
        'snowfall_last_15_mins': 5.0,
        'timestamp': '2025-07-31T12:15:00+00:00'
    }
    mock_get_weather.return_value = weather_reading
    mock_connect.return_value.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = (53.5, 0.1)
    ret = lambda_handler(
        {"location_id": 123, "latitude": 53.5, "longitude": 0.1}, "context")
    cursor.execute.assert_called_once_with(
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
        weather_reading
    )
    assert cursor.execute.call_count == 1
    mock_get_weather.assert_called_once_with(53.5, 0.1)
    mock_connect.return_value.commit.assert_called_once()
    mock_connect.return_value.close.assert_called_once()
    assert ret == {
        "statusCode": 200,
        "message": "Reading successfully inserted."
    }
