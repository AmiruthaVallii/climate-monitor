# pylint: skip-file
import requests
import pandas as pd
from seed_flood_area_assignment import get_flood_area_codes, find_list_of_flood_area_codes_for_location, match_flood_area_codes_to_flood_area_id


def test_get_flood_area_codes_success(requests_mock):

    requests_mock.get('https://environment.data.gov.uk/flood-monitoring/id/floodAreas?lat=51.5074&long=-0.1278&dist=5',
                      json={'items': [{'fwdCode': 'A123'}, {'fwdCode': 'B456'}]})

    lat, lon = 51.5074, -0.1278
    flood_area_codes = get_flood_area_codes(lat, lon)

    assert flood_area_codes == ['A123', 'B456']




def test_find_list_of_flood_area_codes_for_location(requests_mock):
    data = {
        'latitude': [51.5074, 51.5074],
        'longitude': [-0.1278, -0.1278]
    }
    df = pd.DataFrame(data)

    requests_mock.get('https://environment.data.gov.uk/flood-monitoring/id/floodAreas?lat=51.5074&long=-0.1278&dist=5',
                      json={'items': [{'fwdCode': 'A123'}, {'fwdCode': 'B456'}]})

    updated_df = find_list_of_flood_area_codes_for_location(df)

    assert updated_df.shape[0] == 2
    assert 'flood_area_codes' in updated_df.columns
    assert updated_df['flood_area_codes'][0] == [
        'A123', 'B456']


def test_match_flood_area_codes_to_flood_area_id():
    data = {
        'latitude': [51.5074],
        'longitude': [-0.1278],
        'flood_area_codes': [['A123', 'B456']]
    }
    df = pd.DataFrame(data)

    mapping_dict = {'A123': 1, 'B456': 2}

    updated_df = match_flood_area_codes_to_flood_area_id(df, mapping_dict)

    assert 'flood_area_codes_ids' in updated_df.columns
    assert updated_df['flood_area_codes_ids'].iloc[
        0] == 1
    assert updated_df['flood_area_codes_ids'].iloc[
        1] == 2
