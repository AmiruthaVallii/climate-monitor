"""Lambda function for sending daily summary emails."""
import os
from time import sleep
from typing import Any
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "eu-west-2"
CHARSET = "UTF-8"
SENDER = "ecointel.alerts@gmail.com"
EMAIL_TIME_DELAY = 1  # Can only send 1 email per second.
load_dotenv()

logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(message)s", level=logging.INFO)


def get_conn():
    """Returns connection to RDS."""
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


def get_weather_summary(location_ids: tuple[int]) -> dict[int, dict]:
    """Get summary statistics for the day."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            ("SELECT "
             "l.location_id, "
             "l.location_name, "
             "MAX(wr.current_temperature) AS max_temp, "
             "MIN(wr.current_temperature) AS min_temp, "
             "AVG(wr.wind_speed) AS avg_wind_speed, "
             "MAX(wr.wind_gust_speed) AS max_wind_gust, "
             "SUM(wr.snowfall_last_15_mins) AS total_snowfall, "
             "SUM(wr.rainfall_last_15_mins) AS total_rainfall "
             "FROM weather_readings AS wr "
             "JOIN locations AS l USING (location_id) "
             "WHERE l.location_id IN %s "
             "AND timestamp > CURRENT_TIMESTAMP - interval '24 hours' "
             "GROUP BY l.location_id, l.location_name;"),
            (location_ids,))
        data = cur.fetchall()
        summary_stats = {}
        for location in data:
            summary_stats[location["location_id"]] = location
        return summary_stats
    except Exception as e:
        logging.error("Error: %s", str(e))
        raise e
    finally:
        conn.close()


def get_air_quality_summary(location_ids: tuple[int]) -> dict[int, dict]:
    """Get summary statistics for the day."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            ("SELECT "
             "l.location_id, "
             "l.location_name, "
             "AVG(ozone) AS ozone, "
             "AVG(nitrogen_dioxide) AS nitrogen_dioxide, "
             "AVG(sulphur_dioxide) AS sulphur_dioxide, "
             "AVG(pm2_5) AS pm2_5, "
             "AVG(pm10) AS pm10 "
             "FROM air_quality_readings AS a "
             "JOIN locations AS l USING (location_id) "
             "WHERE l.location_id IN %s "
             "AND timestamp > CURRENT_TIMESTAMP - interval '24 hours' "
             "GROUP BY l.location_id, l.location_name;"),
            (location_ids,))
        data = cur.fetchall()
        summary_stats = {}
        for location in data:
            summary_stats[location["location_id"]] = location
        return summary_stats
    except Exception as e:
        logging.error("Error: %s", str(e))
        raise e
    finally:
        conn.close()


def get_mailing_lists() -> dict[int, list[str]]:
    """Get mailing lists for each location with location_id as the key."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(("SELECT la.location_id, ARRAY_AGG(u.email) AS emails "
                     "FROM location_assignment AS la "
                     "JOIN users AS u USING (user_id) "
                     "WHERE subscribe_to_summary = TRUE "
                     "GROUP BY la.location_id;"))
        data = cur.fetchall()
        mailing_lists = {}
        for location in data:
            mailing_lists[location["location_id"]] = location["emails"]
        return mailing_lists
    except Exception as e:
        logging.error("Error: %s", str(e))
        raise e
    finally:
        conn.close()


def make_email_text(weather_data: dict) -> str:
    """Make email text."""
    message = f"""
    Summary for {weather_data["location_name"]} in the past 24 hours:
    Maximum temperature: {weather_data["max_temp"]:.1f}°C
    Total rainfall: {weather_data["total_rainfall"]:.1f} mm
    Maximum wind gust: {weather_data["max_wind_gust"]:.1f} km/h
    """
    return message


def get_severity_band(concentration: float, pollutant: str, text: bool) -> str:
    """Get colour or text band for pollutant level."""
    if text:
        low = "Low"
        moderate = "Moderate"
        high = "High"
        very_high = "Very High"
    else:
        low = "#2ecc71"
        moderate = "#e67e22"
        high = "#ed151d"
        very_high = "#9300e8"
    limit = {
        "ozone": {"low": 100, "moderate": 160, "high": 240},
        "nitrogen_dioxide": {"low": 200, "moderate": 400, "high": 600},
        "sulphur_dioxide": {"low": 266, "moderate": 532, "high": 1065},
        "pm2_5": {"low": 35, "moderate": 53, "high": 70},
        "pm10": {"low": 50, "moderate": 75, "high": 100}
    }
    if concentration <= limit[pollutant]["low"]:
        return low
    if concentration <= limit[pollutant]["moderate"]:
        return moderate
    if concentration <= limit[pollutant]["high"]:
        return high
    return very_high


def get_email_html(weather: dict, air_quality: dict) -> str:
    """Make a nicely formatted html email."""
    message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <title>Daily Weather & Air Quality Summary</title>
    </head>
    <body style="margin:0; padding:0; font-family:Arial, sans-serif; background-color:#f4f4f4;">

    <table align="center" cellpadding="0" cellspacing="0" width="600" style="border-collapse:collapse; background-color:#ffffff; margin-top:20px;">

        <!-- Header -->
        <tr>
        <td align="center" bgcolor="#4a90e2" style="padding: 20px 0; color: #ffffff;">
            <h1 style="margin: 0;">🌤️ Daily Weather & Air Quality Report</h1>
            <p style="margin: 5px 0; font-size: 14px;">Last 24 Hours Summary</p>
        </td>
        </tr>

        <!-- Weather Summary -->
        <tr>
        <td style="padding: 20px;">
            <h2 style="margin-bottom: 10px; color: #333;">Weather Summary</h2>
            <table width="100%" cellpadding="5" cellspacing="0" style="border-collapse:collapse;">
            <tr>
                <td style="border-bottom:1px solid #ddd;">🌡️ Max Temperature:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["max_temp"]:.1f}°C</td>
            </tr>
            <tr>
                <td style="border-bottom:1px solid #ddd;">🧊 Min Temperature:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["min_temp"]:.1f}°C</td>
            </tr>
            <tr>
                <td style="border-bottom:1px solid #ddd;">🌬️ Average Wind Speed:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["avg_wind_speed"]:.1f} km/h</td>
            </tr>
            <tr>
                <td style="border-bottom:1px solid #ddd;">🌬️ Max Wind Gust:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["max_wind_gust"]:.1f} km/h</td>
            </tr>
            <tr>
                <td style="border-bottom:1px solid #ddd;">🌧️ Rainfall:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["total_rainfall"]:.1f} km/h</td>
            </tr>
            <tr>
                <td style="border-bottom:1px solid #ddd;">❄️ Snowfall:</td>
                <td align="right" style="border-bottom:1px solid #ddd;">
                {weather["total_snowfall"]:.1f} cm</td>
            </tr>
            </table>
        </td>
        </tr>

        <!-- Air Quality Section -->
        <tr>
        <td style="padding: 20px;">
            <h2 style="margin-bottom: 10px; color: #333;">Air Quality Summary</h2>
            <table width="100%" cellpadding="5" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background-color:#f0f0f0;">
                <th align="left">Pollutant</th>
                <th align="right">Max Concentration</th>
                <th align="right">Band</th>
            </tr>
            <tr>
                <td>O₃</td>
                <td align="right">{air_quality["ozone"]:.1f} µg/m³</td>
                <td align="right" style="color:{get_severity_band(air_quality["ozone"], "ozone", False)};">
                {get_severity_band(air_quality["ozone"], "ozone", True)}</td>
            </tr>
            <tr>
                <td>NO₂</td>
                <td align="right">{air_quality["nitrogen_dioxide"]:.1f} µg/m³</td>
                <td align="right" style="color:{get_severity_band(air_quality["nitrogen_dioxide"], "nitrogen_dioxide", False)};">
                {get_severity_band(air_quality["nitrogen_dioxide"], "nitrogen_dioxide", True)}</td>
            </tr>
            <tr>
                <td>SO₂</td>
                <td align="right">{air_quality["sulphur_dioxide"]:.1f} µg/m³</td>
                <td align="right" style="color:{get_severity_band(air_quality["sulphur_dioxide"], "sulphur_dioxide", False)};">
                {get_severity_band(air_quality["sulphur_dioxide"], "sulphur_dioxide", True)}</td>
            </tr>
            <tr>
                <td>PM2.5</td>
                <td align="right">{air_quality["pm2_5"]:.1f} µg/m³</td>
                <td align="right" style="color:{get_severity_band(air_quality["pm2_5"], "pm2_5", False)};">
                {get_severity_band(air_quality["pm2_5"], "pm2_5", True)}</td>
            </tr>
            <tr>
                <td>PM10</td>
                <td align="right">{air_quality["pm10"]:.1f} µg/m³</td>
                <td align="right" style="color:{get_severity_band(air_quality["pm10"], "pm10", False)};">
                {get_severity_band(air_quality["pm10"], "pm10", True)}</td>
            </tr>
            </table>
        </td>
        </tr>
    </table>
    </body>
    </html>
    """
    return message


def send_email(addresses: list[str], subject: str, text: str, html: str, ses) -> None:
    """Send the email to `addresses`."""
    for address in addresses:
        try:
            response = ses.send_email(
                Destination={
                    'ToAddresses': [address,]
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': CHARSET,
                            'Data': text,
                        },
                        'Html': {
                            'Charset': CHARSET,
                            'Data': html,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': subject,
                    },
                },
                Source=SENDER,
            )
        except ClientError as e:
            logging.error(e.response['Error']['Message'])
        else:
            logging.info("Email sent! Message ID: %s", response['MessageId'])
            sleep(EMAIL_TIME_DELAY)


def handler(event: dict, context: Any) -> None:  # pylint: disable=unused-argument
    """AWS Lambda handler to send daily summary email."""
    try:
        mailing_lists = get_mailing_lists()
        logging.info("Retrieved mailing lists: %s", mailing_lists)
        weather_summary = get_weather_summary(tuple(mailing_lists.keys()))
        logging.info("Retrieved weather summary from RDS.")
        air_quality_summary = get_air_quality_summary(
            tuple(mailing_lists.keys()))
        logging.info("Retrieved air quality summary from RDS.")
        client = boto3.client('ses', region_name=AWS_REGION)
        for location_id, mailing_list in mailing_lists.items():
            message_text = make_email_text(weather_summary[location_id])
            message_html = get_email_html(
                weather_summary[location_id], air_quality_summary[location_id])
            send_email(
                addresses=mailing_list,
                subject=("Daily summary for " +
                         weather_summary[location_id]["location_name"]),
                text=message_text,
                html=message_html,
                ses=client
            )
            logging.info("Sent emails for location_id: %s", location_id)
        return {
            "statusCode": 200,
            "message": "Sent all emails."
        }
    except Exception as e:
        logging.error("Error: %s", str(e))
        raise e


if __name__ == "__main__":
    handler(1, 1)
