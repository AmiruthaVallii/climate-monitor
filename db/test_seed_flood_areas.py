import requests
from seed_flood_areas import get_codes, ENDPOINT


def test_get_codes(requests_mock):
    requests_mock.get(ENDPOINT,
                      json={'items': [{'fwdCode': 'A123'}, {'fwdCode': 'B456'}]})
    codes = get_codes()
    assert requests_mock.called
    assert requests_mock.call_count == 1
    assert codes == ['A123', 'B456']
