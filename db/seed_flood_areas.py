"""seeds the flood area codes into flood_areas"""
import requests
from psycopg2 import connect
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import dotenv_values

ENDPOINT = 'https://environment.data.gov.uk/flood-monitoring/id/floodAreas?_limit=6000'
# limit must be provided for endpoint unless api will return first 500 codes (there are around 4200)


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


def get_codes() -> list[str]:
    """finds all flood area codes from endpoints"""
    response = requests.get(ENDPOINT)
    response = response.json()
    areas = response['items']
    flood_area_codes = []
    for area in areas:
        flood_area_codes.append(area['fwdCode'])
    return flood_area_codes


def insert_codes(config, code_list: list[str]) -> None:
    """inserts area codes into database"""
    conn = get_connection(config)
    cur = conn.cursor()
    clear_query = "DELETE FROM flood_areas;"
    cur.execute(clear_query)
    cur.execute("SELECT SETVAL('flood_areas_flood_area_id_seq',1,false);")
    query = 'INSERT INTO flood_areas (flood_area_code) ' \
            'VALUES %s'
    execute_values(cur, query, [(code,) for code in code_list])
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    config = dotenv_values()
    codes = get_codes()
    insert_codes(config, codes)
