import requests
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime
from dotenv import load_dotenv

ENDPOINT = 'https://climate-api.open-meteo.com/v1/climate?latitude=52.52&longitude=13.41&start_date=1950-01-01&end_date=2050-12-31&models=EC_Earth3P_HR&daily=temperature_2m_max,temperature_2m_mean,temperature_2m_min,wind_speed_10m_mean,wind_speed_10m_max,rain_sum,snowfall_sum'


def get_conn():
    """connects to db"""
    conn = connect(user=config_values['USER'],
                   password=config_values['DBPASSWORD'],
                   dbname=config_values['DBNAME'],
                   port=config_values['PORT'],
                   host=config_values['HOST'],
                   sslmode="require",
                   cursor_factory=RealDictCursor)
    return conn


def extract_future_data(location_id: int, lat: float, lon: float, start: str, end: str) -> list:
    url = f'https://climate-api.open-meteo.com/v1/climate?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}&models=EC_Earth3P_HR&daily=temperature_2m_max,temperature_2m_mean,temperature_2m_min,wind_speed_10m_mean,wind_speed_10m_max,rain_sum,snowfall_sum'
    response = requests.get(url)
    response = response.json()
    data = response['daily']
    rows = []
    for date, mean_temp, max_temp, min_temp, total_rain, total_snow, mean_wind, max_wind in zip(data['time'], data['temperature_2m_mean'], data['temperature_2m_max'], data['temperature_2m_min'], data['rain_sum'], data['snowfall_sum'], data['wind_speed_10m_mean'], data['wind_speed_10m_max']):
        try:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            mean_temp = float(mean_temp)
            max_temp = float(max_temp)
            min_temp = float(min_temp)
            total_rain = float(total_rain)
            total_snow = float(total_snow)
            mean_wind = float(mean_wind)
            max_wind = float(max_wind)
            rows.append(date, location_id, mean_temp, max_temp,
                        min_temp, total_rain, total_snow, mean_wind, max_wind)
        except (ValueError, TypeError):
            continue
    return rows


def insert_rows(data: list):
    query = 'INSERT INTO future_weather_prediction (date, location_id, mean_temperature, max_temperature, min_temperature, total_rainfall, total_snowfall, mean_wind_speed, max_wind_speed) ' \
        'VALUES %s'
    conn = get_conn()
    cur = conn.cursor()
    try:
        execute_values(cur, query, data)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def lambda_handler(event: dict, context: Any) -> dict:  # pylint: disable=unused-argument
    """
    Uploads future weather predictions weather data for given location_id and date range.
    Parameters:
        event: Dict containing the location_id, start_date and end_date 
            e.g. {"location_id": 1, "latitude": 51.507351, "longitude": -0.127758,
                  "start_date": "1940-01-01", "end_date": "1960-01-01"}
        context: Lambda runtime context
    Returns:
        Dict containing status message
    """
    rows = extract_future_data(event['location_id'], event['latitude'],
                               event['longitude'], event['start_date'], event['end_date'])
    insert_rows()
