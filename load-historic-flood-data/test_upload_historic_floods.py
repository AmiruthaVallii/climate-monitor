import pytest
import pandas as pd

from upload_historic_floods import load_historical_flood_data


def test_load_historical_flood_data(monkeypatch):
    test_df = pd.DataFrame({
        'DATE': ['2006-01-31 13:55:34', '2006-01-31 16:33:10', 'Invalid Date'],
        'AREA': ['SW - Devon', 'SW - North Wessex', 'ANG - Eastern'],
        'CODE': ['113WACT2a', '112WACTAVN', '054WATBT1'],
        'WARNING / ALERT AREA NAME': ['Devon Coast (North)', 'Porlock to Avonmouth', 'Tidal Rivers Bure, Ant and Thurne'],
        'TYPE': ['Flood Warning', 'Severe Flood Warning', 'Flood Alert']
    })

    monkeypatch.setattr(pd, "read_excel", lambda filename: test_df)

    result = load_historical_flood_data("test.ods")

    assert len(result) == 2
    assert set(result['TYPE']) == {'Flood Warning', 'Severe Flood Warning'}
    assert pd.api.types.is_datetime64_any_dtype(result['DATE'])
    assert not result['DATE'].isna().any()
