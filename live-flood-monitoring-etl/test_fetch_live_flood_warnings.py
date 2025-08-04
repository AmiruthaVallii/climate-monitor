from datetime import datetime
import pytest
from unittest.mock import patch
from fetch_live_flood_warnings import fetch_flood_data, transform_data


@patch("fetch_live_flood_warnings.requests.get")
def test_fetch_flood_data_returns_list(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"items": [{"id": "flood1"}]}

    result = fetch_flood_data()
    assert isinstance(result, list)
    assert result == [{"id": "flood1"}]


def test_transform_data_skips_unmapped_data():
    items = [{
        "severityLevel": "3",
        "floodAreaID": "XYZ123",
        "timeMessageChanged": "2023-01-01T12:00:00",
        "timeSeverityChanged": "2023-01-01T11:00:00",
        "message": "Test warning",
        "description": "Test location"
    }]
    severity_map = {}  # no matching severity
    area_map = {}  # no matching area
    existing_keys = set()

    result = transform_data(items, severity_map, area_map, existing_keys)
    assert result == []


def test_transform_data_valid_case():
    items = [{
        "severityLevel": "3",
        "floodAreaID": "XYZ123",
        "timeMessageChanged": "2023-01-01T12:00:00",
        "timeSeverityChanged": "2023-01-01T11:00:00",
        "message": "Flood risk",
        "description": "River Thames"
    }]
    severity_map = {"3": 1}
    area_map = {"XYZ123": 2}
    existing_keys = set()

    result = transform_data(items, severity_map, area_map, existing_keys)

    assert len(result) == 1
    assert isinstance(result[0], tuple)
    assert result[0][0] == 2  # flood_area_id
    assert result[0][2] == 1  # severity_id
