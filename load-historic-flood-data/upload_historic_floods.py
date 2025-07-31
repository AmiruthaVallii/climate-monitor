import os
import logging
import pandas as pd
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()

HISTORIC_DATA_FILENAME = 'historical_flood_warnings_data.ods'


def config_logger() -> None:
    """Configures logger."""

    logging.basicConfig(level=logging.INFO,
                        format='%(levelname)s: %(message)s')


def get_conn():
    """Returns connection to RDS Postgres Database."""

    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


def get_cursor(connection):
    """Returns cursor object."""
    return connection.cursor()


def close_connection(connection, cursor):
    """Commits changes and closes cursor and connection to database."""
    connection.commit()
    cursor.close()
    connection.close()


def load_historical_flood_data(filename: str) -> pd.DataFrame:
    """Loads historic flood data into pandas dataframe.
        - filters data for only 'Flood Warning' 
            and 'Severe Flood Warning'."""

    df = pd.read_excel(filename)

    filtered_df = df[df['TYPE'].isin(
        ['Severe Flood Warning', 'Flood Warning'])].copy()

    filtered_df['DATE'] = pd.to_datetime(filtered_df['DATE'], errors='coerce')

    filtered_df = filtered_df.dropna(subset=['DATE'])

    return filtered_df


def get_flood_severity_info(connection) -> pd.DataFrame:
    """Fetches flood severity information from database."""

    return pd.read_sql(
        "SELECT severity_id, severity_name FROM flood_severity", connection)


def get_flood_area_info(connection) -> pd.DataFrame:
    """Fetches flood area information from database."""

    return pd.read_sql(
        "SELECT flood_area_id, flood_area_code FROM flood_areas", connection)


def transform_historical_flood_data(flood_df: pd.DataFrame, severity_df: pd.DataFrame, flood_area_df: pd.DataFrame) -> list[list]:
    """Prepares historical flood data for upload by finding the matching severity_id and flood_area_id for each row."""

    merged = (
        flood_df
        .merge(severity_df, left_on='TYPE', right_on='severity_name', how='left')
        .merge(flood_area_df, left_on='CODE', right_on='flood_area_code', how='left')
    )

    merged = merged.dropna(subset=['severity_id', 'flood_area_id'])

    return merged[[
        'DATE', 'flood_area_id', 'severity_id']].values.tolist()


def upload_historical_flood_data(data_to_insert: list[list], cursor) -> None:
    """Uploads all historical flood data to the historical_floods table in database."""

    execute_values(
        cursor,
        """
            INSERT INTO historical_floods (date, flood_area_id, severity_id)
            VALUES %s
        """,
        data_to_insert
    )


if __name__ == "__main__":

    config_logger()

    conn = get_conn()
    cur = get_cursor(conn)

    try:
        logging.info("Loading historical flood data...")
        historic_flood_data = load_historical_flood_data(
            HISTORIC_DATA_FILENAME)

        flood_severity_df = get_flood_severity_info(conn)
        flood_area_df = get_flood_area_info(conn)

        transformed_historic_flood_data = transform_historical_flood_data(
            historic_flood_data, flood_severity_df, flood_area_df)

        logging.info(
            "Inserting %d records into database...", len(transformed_historic_flood_data))
        upload_historical_flood_data(transformed_historic_flood_data, cur)
        logging.info("Data upload complete.")

    finally:
        close_connection(conn, cur)
        logging.info("Database connection closed.")
