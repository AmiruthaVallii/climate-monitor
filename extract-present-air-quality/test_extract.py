from unittest.mock import patch, Mock, call
from requests import Session
from extract import get_air_quality, lambda_handler


@patch.object(Session, 'get')
def test_get_air_quality(mock_session, response_payload, expected_return):
    response = Mock()
    mock_session.return_value = response
    response.json.return_value = response_payload
    ret = get_air_quality(76.4, 23.5)
    assert ret == expected_return


@patch("extract.get_air_quality")
@patch("psycopg2.connect")
def test_lambda_handler(mock_connect, mock_get_air_quality, expected_return):
    cursor = Mock()
    mock_get_air_quality.return_value = expected_return
    mock_connect.return_value.cursor.return_value.__enter__.return_value = cursor
    cursor.fetchone.return_value = (53.5, 0.1)
    ret = lambda_handler({"location_id": 47}, "context")
    cursor.execute.assert_has_calls([call("SELECT latitude, longitude FROM locations WHERE location_id = %s", (47,)),
                                     call(("INSERT INTO air_quality_readings "
                                           "(timestamp, location_id, air_quality_index,"
                                           "carbon_monoxide, nitrogen_monoxide, ammonia, "
                                           "nitrogen_dioxide, ozone, sulphur_dioxide, "
                                           "pm2_5, pm10) "
                                           "VALUES "
                                           "(%(timestamp)s, %(location_id)s, %(air_quality_index)s,"
                                           "%(carbon_monoxide)s, %(nitrogen_monoxide)s, %(ammonia)s, "
                                           "%(nitrogen_dioxide)s, %(ozone)s, %(sulphur_dioxide)s, "
                                           "%(pm2_5)s, %(pm10)s)"),
                                          expected_return | {"location_id": 47})
                                     ])
    assert cursor.execute.call_count == 2
    mock_get_air_quality.assert_called_once_with(53.5, 0.1)
    mock_connect.return_value.commit.assert_called_once()
    mock_connect.return_value.close.assert_called_once()
    assert ret == {
        "statusCode": 200,
        "message": "Reading successfully inserted."
    }
