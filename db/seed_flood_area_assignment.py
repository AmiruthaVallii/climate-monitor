"""seeds the flood_area_assignment table with location_ids and their corresponding flood_area_ids"""

import requests
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import dotenv_values
import pandas as pd
import logging

RADIUS = 5


def get_connection(config_values):
    """connects to db"""
    conn = connect(user=config_values['USER'],
                   password=config_values['DBPASSWORD'],
                   dbname=config_values['DBNAME'],
                   port=config_values['PORT'],
                   host=config_values['HOST'],
                   sslmode="require",
                   cursor_factory=RealDictCursor)
    return conn


def get_location_ids_lat_long(config_values) -> pd.DataFrame:
    """Get's all the locations in the database"""
    conn = get_connection(config_values)
    cur = conn.cursor()
    try:
        cur.execute('select location_id, latitude,longitude from locations;')
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
        return df
    finally:
        cur.close()
        conn.close()


def get_flood_area_codes(lat: float, lon: float) -> list[str]:
    """Get's the flood area codes for a given latitude and longitude"""
    endpoint = f'https://environment.data.gov.uk/flood-monitoring/id/floodAreas?lat={lat}&long={lon}&dist={RADIUS}'
    try:
        response = requests.get(endpoint)
        response = response.json()
        areas = response['items']
        flood_area_codes = []
        for area in areas:
            flood_area_codes.append(area['fwdCode'])
        return flood_area_codes
    except requests.exceptions.RequestException:
        logging.error("Endpoint request exception")
        return {"error": "Request Exception"}


def find_list_of_flood_area_codes_for_location(df: pd.DataFrame) -> pd.DataFrame:
    """get's the flood area codes for each location in a dataframe"""
    codes = []
    for index, row in df.iterrows():
        lat, lon = row['latitude'], row['longitude']
        area_codes = get_flood_area_codes(lat, lon)
        codes.append(area_codes)

    df['flood_area_codes'] = codes
    return df


def get_flood_area(config_values) -> dict:
    """returns a dictionary of flood area codes to their id"""
    conn = get_connection(config_values)
    cur = conn.cursor()
    try:
        cur.execute('select flood_area_code,flood_area_id from flood_areas;')
        results = cur.fetchall()
        results_dict = {result['flood_area_code']                        : result["flood_area_id"] for result in results}
        return results_dict
    finally:
        cur.close()
        conn.close()


def match_flood_area_codes_to_flood_area_id(df: pd.DataFrame, mapping_dict: dict) -> pd.DataFrame:
    """finds the flood_area_ids in our database and maps 
    them to the flood_area_codes in the dataframe """

    df['flood_area_codes_ids'] = df['flood_area_codes'].apply(
        lambda x: [mapping_dict.get(val) for val in x])
    df = df.explode('flood_area_codes_ids')
    df = df.dropna(subset=['flood_area_codes_ids'])
    df = df.drop('latitude', axis=1, errors='ignore')
    df = df.drop('longitude', axis=1, errors='ignore')
    df = df.drop('flood_area_codes', axis=1, errors='ignore')
    return df


def insert_into_flood_assignment(df, config_values):
    """inserts location_id's and their flood_area_ids into the database"""
    data = list(df.itertuples(index=False, name=None))
    conn = get_connection(config_values)
    cur = conn.cursor()
    try:
        query = 'INSERT INTO flood_area_assignment (location_id, flood_area_id) ' \
                'VALUES %s'
        execute_values(cur, query, data)
        conn.commit()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    config = dotenv_values()
    locations = get_location_ids_lat_long(config)
    flood_codes_df = find_list_of_flood_area_codes_for_location(locations)
    flood_area_dict = get_flood_area(config)
    flood_ids_df = match_flood_area_codes_to_flood_area_id(
        flood_codes_df, flood_area_dict)
    print(flood_ids_df)
    insert_into_flood_assignment(flood_ids_df, config)
