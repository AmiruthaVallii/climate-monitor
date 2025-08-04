"""Lambda handler that checks the UK Flood Monitoring API and uploads data to `flood_warnings` table in RDS"""

import os
import logging
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = 'https://environment.data.gov.uk/flood-monitoring/id/floods'


def config_logger():
    """Configures logger."""

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")


def get_conn():
    """Returns connection to the PostgreSQL RDS."""

    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


def fetch_flood_data() -> list[dict]:
    """Fetches data from Environment Agency Flood Monitoring API."""

    response = requests.get(ENDPOINT, timeout=10)
    response.raise_for_status()
    return response.json().get("items", [])


def get_mappings(conn) -> tuple[dict, dict]:
    """Fetches severity levels and flood areas."""

    with conn.cursor() as cur:
        cur.execute("SELECT severity_level, severity_id FROM flood_severity;")
        severity_map = dict(cur.fetchall())

        cur.execute("SELECT flood_area_code, flood_area_id FROM flood_areas;")
        area_map = dict(cur.fetchall())

    return severity_map, area_map


def fetch_existing_warnings(conn) -> set:
    """Gets existing (flood_area_id, updated_at) pairs to avoid duplicate inserts."""

    with conn.cursor() as cur:
        cur.execute("SELECT flood_area_id, updated_at FROM flood_warnings;")
        return set(cur.fetchall())


def transform_data(items, severity_map, area_map, existing_keys: set) -> list[tuple]:
    """Transforms raw API data, filtered for new entries only."""

    new_records = []

    for item in items:
        severity_level = item.get("severityLevel")
        flood_area_code = item.get("floodAreaID")

        severity_id = severity_map.get(severity_level)
        flood_area_id = area_map.get(flood_area_code)

        if not severity_id or not flood_area_id:
            continue  # skip if mappings not found

        time_msg_changed = item.get("timeMessageChanged")
        time_sev_changed = item.get("timeSeverityChanged")

        if not time_msg_changed or not time_sev_changed:
            continue

        updated_at = max(datetime.fromisoformat(time_msg_changed),
                         datetime.fromisoformat(time_sev_changed))

        # skip if record already exists
        if (flood_area_id, updated_at) in existing_keys:
            continue

        new_records.append((
            flood_area_id,
            updated_at,
            severity_id,
            item.get("message"),
            False,  # notifications_sent
            item.get("description")
        ))

    return new_records


def insert_flood_data(records):
    """Uploads flood data to `flood_warnings` table in RDS. """

    insert_query = """
        INSERT INTO flood_warnings (
            flood_area_id, updated_at, severity_id, message,
            notifications_sent, location_description
        ) VALUES %s;
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, insert_query, records)
        logging.info("Inserted %d new flood warnings.", len(records))


def lambda_handler(event=None, context=None):  # pylint: disable=unused-argument

    config_logger()

    logging.info("Starting live flood monitoring Lambda...")

    try:
        api_response = fetch_flood_data()

        if not api_response:
            logging.info("No flood warnings found in API.")

            return {
                "statusCode": 200,
                "body": "No flood warnings found in API."
            }

        with get_conn() as connection:
            severity_map, flood_area_map = get_mappings(connection)

            logging.info("Fetching existing flood warnings in RDS...")
            existing_records = fetch_existing_warnings(connection)

            new_flood_records = transform_data(
                api_response, severity_map, flood_area_map, existing_records)

            if not new_flood_records:
                logging.info("No new flood warnings to insert.")
            else:
                insert_flood_data(new_flood_records)
                logging.info("Flood warnings upload complete.")

        return {
            "statusCode": 200,
            "body": f"{len(new_flood_records)} flood warnings uploaded."
        }

    except Exception as e:
        logging.error("Error in Lambda execution: %s", e)
        raise e
