import pytest
import pandas as pd
import numpy as np


@pytest.fixture()
def expected_return():
    data = {
        "timestamp": pd.date_range(
            start=pd.to_datetime(-946339200, unit="s", utc=True),
            end=pd.to_datetime(-946166400, unit="s", utc=True),
            freq=pd.Timedelta(seconds=3600),
            inclusive="left"
        ),
        "hourly_temperature": np.linspace(9, 10, 48),
        "hourly_wind_speed": np.linspace(9, 10, 48),
        "hourly_wind_direction": np.linspace(9, 10, 48),
        "hourly_wind_gust_speed": np.linspace(9, 10, 48),
        "hourly_rainfall": np.linspace(9, 10, 48),
        "hourly_snowfall": np.linspace(9, 10, 48),
    }
    return pd.DataFrame(data)
