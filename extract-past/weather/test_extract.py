from unittest.mock import MagicMock, Mock, patch, call
import numpy as np
from extract import get_weather, lambda_handler


@patch("openmeteo_requests.Client")
def test_get_weather(api_mock, expected_return):
    hourly_weather_mock = Mock()
    response_mock = Mock()
    openmeteo = Mock()
    response_mock.Hourly.return_value = hourly_weather_mock
    hourly_weather_mock.Variables.return_value.ValuesAsNumpy.side_effect = [
        np.linspace(9, 10, 48),
        np.linspace(9, 10, 48),
        np.linspace(9, 10, 48),
        np.linspace(9, 10, 48),
        np.linspace(9, 10, 48),
        np.linspace(9, 10, 48),
    ]
    hourly_weather_mock.Time.return_value = -946339200
    hourly_weather_mock.TimeEnd.return_value = -946166400
    hourly_weather_mock.Interval.return_value = 3600
    api_mock.return_value = openmeteo
    openmeteo.weather_api.return_value = [response_mock]
    ret = get_weather(51.507351, -0.127758, "1940-01-06", "1940-01-07")
    openmeteo.weather_api.assert_called_once_with(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": 51.507351,
            "longitude": -0.127758,
            "start_date": "1940-01-06",
            "end_date": "1940-01-07",
            "hourly": ["temperature_2m", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "rain", "snowfall"],
        }
    )
    assert ret.equals(expected_return)


@patch("extract.get_engine")
@patch("extract.get_weather")
def test_lambda_handler(mock_get_weather, mock_get_engine):
    engine = Mock()
    mock_get_engine.return_value = engine
    mock_df = Mock()
    mock_df.__setitem__ = Mock(return_value=False)
    mock_get_weather.return_value = mock_df
    ret = lambda_handler({"location_id": 1, "latitude": 51.507351, "longitude": -0.127758,
                          "start_date": "1940-01-06", "end_date": "1940-01-07"},
                         "context")
    mock_get_engine.assert_called_once()
    mock_df.__setitem__.assert_called_once_with("location_id", 1)
    mock_df.to_sql.assert_called_once_with("historical_weather_readings",
                                           engine,
                                           if_exists="append",
                                           index=False,
                                           method="multi")
    assert ret == {
        "statusCode": 200,
        "message": "Historical weather data successfully inserted."
    }
