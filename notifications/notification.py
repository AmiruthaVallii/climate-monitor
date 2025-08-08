"""
Script to alert users to any relevant weather events
"""

import os
from datetime import datetime, timedelta, timezone, date
import logging
import time
from typing import Any

from dotenv import load_dotenv
import psycopg2
import pandas as pd
import boto3

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

TEMPERATURE_THRESHOLD = 28
RAIN_THRESHOLD = 3
WIND_THRESHOLD = 64
AQI_THRESHOLD = 3


def get_connection() -> psycopg2.extensions.connection:
    """Get connection to RDS."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dbname=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT")
    )


def get_unsent_flood_warnings() -> pd.DataFrame:
    """Connect to the DB and retrieve all flood warnings that have not been sent yet"""
    try:
        with get_connection() as conn:
            logging.info("Connected to database.")
            query = """
            SELECT
                fw.flood_warnings_id,
                fw.updated_at,
                fw.location_description,
                fw.message,
                l.location_name,
                u.email,
                fs.severity_meaning
            FROM flood_warnings fw
            JOIN flood_area_assignment faa  USING (flood_area_id)
            JOIN locations l USING (location_id )
            JOIN location_assignment la USING (location_id)
            JOIN users u USING (user_id )
            JOIN flood_severity fs USING (severity_id)
            WHERE la.subscribe_to_alerts = TRUE
            AND fw.notifications_sent = FALSE;
            """
        return pd.read_sql_query(query, conn)
    except:
        raise RuntimeError("Unable to connect to RDS")


def get_weather_readings() -> pd.DataFrame:
    """Get most recent weather readings"""
    try:
        with get_connection() as conn:
            query = f"""
            SELECT l.location_name, wr.rainfall_last_15_mins, wr.current_temperature, wr.wind_speed, u.email
            FROM weather_readings wr
            JOIN locations l USING (location_id)
            JOIN location_assignment la USING (location_id)
            JOIN users u USING (user_id )
            WHERE wr."timestamp" > '{datetime.now(timezone.utc) - timedelta(minutes=15)}'
            AND la.subscribe_to_alerts = TRUE;
            """
        return pd.read_sql_query(query, conn)
    except:
        raise RuntimeError("Unable to connect to RDS")


def get_aqi_readings() -> pd.DataFrame:
    """Get most recent Air Quality Index readings"""
    try:
        with get_connection() as conn:
            query = f"""
            SELECT l.location_name, aqr.air_quality_index, u.email
            FROM air_quality_readings aqr
            JOIN locations l USING (location_id)
            JOIN location_assignment la USING (location_id)
            JOIN users u USING (user_id )
            WHERE aqr."timestamp" > '{datetime.now(timezone.utc) - timedelta(minutes=15)}'
            AND la.subscribe_to_alerts = TRUE;
            """
        return pd.read_sql_query(query, conn)
    except:
        raise RuntimeError("Unable to connect to RDS")


def check_for_weather_alerts(readings: pd.DataFrame) -> list:
    """Check the weather readings to see if any alerts need to be sent"""
    return_warnings = []
    for reading in readings.itertuples():
        if reading[2] > RAIN_THRESHOLD:
            return_warnings.append(
                ("Rainfall", reading[2], reading[1], reading[5]))
        if reading[3] > TEMPERATURE_THRESHOLD:
            return_warnings.append(
                ("Temperature", reading[3], reading[1], reading[5]))
        if reading[4] > WIND_THRESHOLD:
            return_warnings.append(
                ("Wind", reading[4], reading[1], reading[5]))
    return return_warnings


def check_for_aqi_alert(readings: pd.DataFrame) -> list:
    """Check the air quality readings to see if any alerts needs to be sent"""
    return_warnings = []
    for reading in readings.itertuples():
        if reading[2] > AQI_THRESHOLD:
            return_warnings.append(
                ("Air Quality Index", reading[2], reading[1], reading[3]))
    return return_warnings


def create_flood_message(warning: tuple) -> str:
    """Format HTML for an email alert"""
    return """
    <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>Flood Warning</title>
        <style>
            body {
            font-family: Arial, sans-serif;
            background-color: #fdfdfd;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            }
            .alert-box {
            display: inline-block;
            background-color: #fff8f6;
            color: #333;
            padding: 20px;
            border: 2px solid #cc0000;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(204, 0, 0, 0.1);
            }
            h1 {
            color: #cc0000;
            font-size: 22px;
            margin: 0 0 10px;
            }
            .subtitle {
            font-size: 17px;
            font-weight: bold;
            margin-bottom: 12px;
            }
            .location {
            font-size: 15px;
            margin-bottom: 10px;
            }
            .warning {
            background-color: #ffe5e5;
            padding: 8px;
            border-left: 4px solid #cc0000;
            margin-bottom: 12px;
            font-size: 15px;
            }
            .timestamp {
            font-size: 13px;
            color: #555;
            }
        </style>
        </head>
        <body>
        <div class="alert-box">
            <h1>FLOOD WARNING IN """ + warning[5].upper() + """</h1>
            <div class="subtitle">""" + warning[7] + """</div>
            <div class="location">""" + warning[3] + """</div>
            <div class="warning">""" + warning[4] + """</div>
            <div class="timestamp">Last Updated: """ + str(warning[2]) + """</div>
        </div>
        </body>
    </html>
    """


def create_weather_message(alert: tuple) -> str:
    """Format HTML for an email alert"""
    unit_types = {
        "Rainfall": "mm",
        "Temperature": "°C",
        "Wind": "kph"
    }
    return """
    <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>Weather Alert</title>
        <style>
            body {
            font-family: Arial, sans-serif;
            background-color: #fdfdfd;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            }
            .alert-box {
            display: inline-block;
            background-color: #fff8f6;
            color: #333;
            padding: 20px;
            border: 2px solid #cc0000;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(204, 0, 0, 0.1);
            min-width: 280px;
            }
            h1 {
            color: #cc0000;
            font-size: 22px;
            margin: 0 0 10px;
            }
            .subtitle {
            font-size: 17px;
            font-weight: bold;
            margin-bottom: 12px;
            }
            .message {
            background-color: #ffe5e5;
            padding: 8px;
            border-left: 4px solid #cc0000;
            margin-bottom: 12px;
            font-size: 15px;
            }
            .timestamp {
            font-size: 13px;
            color: #555;
            }
        </style>
        </head>
        <body>
        <div class="alert-box">
            <h1>⚠️ WEATHER WARNING IN """ + alert[2].upper() + """</h1>
            <div class="subtitle">Threshold Exceeded</div>
            <div class="message">The """ + alert[0] + """ has reached a value of <strong>""" + str(alert[1]) + unit_types.get(alert[0]) + """</strong>.</div>
        </div>
        </body>
    </html>

    """


def set_warnings_to_sent(warning: tuple) -> None:
    """Set flood notifications to sent in the database"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                ("""
                 UPDATE flood_warnings
                 SET notifications_sent = TRUE
                 WHERE flood_warnings_id = %s
                 """), (warning[1],))
            conn.commit()
            logging.info(
                "Set notification_sent to TRUE for flood warning %s.", {warning[1]})
    finally:
        conn.close()


def send_flood_notifications(warnings: pd.DataFrame) -> None:
    """Send the flood notifications"""
    client = boto3.client('ses', region_name=os.getenv("AWS_REGION"))
    for warning in warnings.itertuples():
        message = create_flood_message(warning)

        try:
            response = client.send_email(
                Destination={
                    'ToAddresses': [warning[6]],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': message,
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': f'FLOOD WARNING IN {warning[5].upper()}',
                    },
                },
                Source='ecointel.alerts@gmail.com',
            )
            logging.info(response)
            set_warnings_to_sent(warning)
        except:
            logging.info("Unable to send flood notification")
        time.sleep(1)


def check_weather_alert_needs_to_be_sent(alert):
    """Check if any alerts have already been sent that day"""
    column_map = {
        "Rainfall": ("rainfall_last_15_mins", RAIN_THRESHOLD),
        "Temperature": ("current_temperature", TEMPERATURE_THRESHOLD),
        "Wind": ("wind_speed", WIND_THRESHOLD)
    }
    try:
        with get_connection() as conn:
            query = f"""
            SELECT wr.{column_map.get(alert[0])[0]}
            FROM weather_readings wr
            JOIN locations l USING (location_id)
            WHERE wr."timestamp" > '{date.today()}'
            AND l.location_name = '{alert[2]}'
            AND wr.{column_map.get(alert[0])[0]} > {column_map.get(alert[0])[1]};
            """
        return pd.read_sql_query(query, conn)
    except:
        raise RuntimeError("Unable to connect to RDS")


def send_weather_notifications(weather_alerts: list, aqi_alerts: list) -> None:
    """Send weather alerts to users"""
    client = boto3.client('ses')
    alerts = weather_alerts + aqi_alerts

    if not alerts:
        logging.info("No alerts to send for weather or air quality")
        return

    for alert in alerts:
        if len(check_weather_alert_needs_to_be_sent(alert)) > 1:
            continue
        try:
            message = create_weather_message(alert)
            response = client.send_email(
                Destination={
                    'ToAddresses': [alert[3]],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': message,
                        },
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': f'FLOOD WARNING IN {alert[2].upper()}',
                    },
                },
                Source='ecointel.alerts@gmail.com',
            )
            logging.info(response)
        except:
            logging.error("Unable to send weather alert")
        time.sleep(1)


def lambda_handler(event: Any = None, context: Any = None) -> None:  # pylint: disable=unused-argument
    """Allows the Lambda to run the script"""
    warnings = get_unsent_flood_warnings()
    send_flood_notifications(warnings)

    weather_readings = get_weather_readings()
    weather_alerts = check_for_weather_alerts(weather_readings)

    aqi_readings = get_aqi_readings()
    aqi_alerts = check_for_aqi_alert(aqi_readings)

    send_weather_notifications(weather_alerts, aqi_alerts)


if __name__ == "__main__":
    lambda_handler()
