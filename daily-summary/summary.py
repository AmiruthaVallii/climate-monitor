import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

AWS_REGION = "eu-west-2"
CHARSET = "UTF-8"
SENDER = "ecointel.alerts@gmail.com"
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


def get_summary(location_ids: list[int]) -> dict[int, dict]:
    """Get summary statistics for the day."""
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            ("SELECT "
             "l.location_id, "
             "l.location_name, "
             "MAX(wr.current_temperature) AS max_temp, "
             "MAX(wr.wind_gust_speed) AS max_gust_speed, "
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
    finally:
        conn.close()


def make_email_text(weather_data: dict) -> str:
    """Make email text."""
    message = f"""
    Summary for {weather_data["location_name"]} in the past 24 hours:
    Maximum temperature: {weather_data["max_temp"]:.1f}°C
    Total rainfall: {weather_data["total_rainfall"]:.1f} mm
    Maximum wind gust: {weather_data["max_gust_speed"]:.1f} km/h
    """
    return message


def send_email(addresses: list[str], subject: str, text: str, ses) -> None:
    try:
        response = ses.send_email(
            Destination={
                'ToAddresses': addresses
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': text,
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


def handler(event: dict, context) -> None:
    mailing_lists = get_mailing_lists()
    summary = get_summary(tuple(mailing_lists.keys()))
    client = boto3.client('ses', region_name=AWS_REGION)
    for location_id, summary in summary.items():
        message = make_email_text(summary)
        send_email(
            addresses=mailing_lists[location_id],
            subject="Daily summary for " + summary["location_name"],
            text=message,
            ses=client
        )


if __name__ == "__main__":
    handler(1, 1)
