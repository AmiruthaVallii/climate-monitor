import requests
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import dotenv_values
import pandas as pd
ENDPOINT = 'https://environment.data.gov.uk/flood-monitoring/id/floodAreas?lat=y&long=x&dist=d'


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


def get_location_ids_lat_long(config_values):
    conn = get_connection(config_values)
    cur = conn.cursor()
    cur.execute('select location_id, latitude,longitude from locations;')
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=columns)
    return df


def find_list_of_flood_area_codes_for_location():
    pass


def match_flood_area_codes_to_flood_area_id():
    pass


def insert_into_flood_assignment():
    pass
