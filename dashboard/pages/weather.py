# pylint: disable=import-error
"""Weather Dashboard"""
import os
import datetime as dt
import pandas as pd

import psycopg2
from dotenv import load_dotenv
import altair as alt
import streamlit as st
from modules.nav import navbar


def get_connection():
    """get rds connection"""
    load_dotenv()
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
        port=5432)
    return conn


@st.cache_data(ttl="300")
def load_recent_weather(location_id):
    """loads recent weather from rds"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "select * from weather_readings WHERE location_id = %s"
        parameter = (location_id,)
        cur.execute(query, parameter)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
        return df


@st.cache_data()
def load_past_weather(location_id):
    """loads past weather from rds"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "select * from historical_weather_readings WHERE location_id = %s"
        parameter = (location_id,)
        cur.execute(query, parameter)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
        return df


@st.cache_data()
def load_future_weather(location_id):
    """loads future weather from rds"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "select * from future_weather_prediction WHERE location_id = %s"
        parameter = (location_id,)

        cur.execute(query, parameter)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
        return df


@st.cache_data()
def load_locations():
    """loads locations from rds"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "select location_id, location_name from locations"
        cur.execute(query)
        rows = cur.fetchall()
        locations_df = pd.DataFrame(
            rows, columns=["location_id", "location_name"])
    finally:
        cur.close()
        conn.close()
        return locations_df


def prepare_temperature_data(selected_location_id):
    """Prepare temperature data for visualization"""

    recent_df = load_recent_weather(selected_location_id)
    historical_df = load_past_weather(selected_location_id)
    future_df = load_future_weather(selected_location_id)

    recent_filtered = recent_df[recent_df['location_id']
                                == selected_location_id].copy()
    historical_filtered = historical_df[historical_df['location_id']
                                        == selected_location_id].copy()
    future_filtered = future_df[future_df['location_id']
                                == selected_location_id].copy()

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])
        recent_filtered['day_of_year'] = recent_filtered['timestamp'].dt.dayofyear

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    datasets = []

    current_year = dt.datetime.now().year
    if not recent_filtered.empty:
        current_temp = recent_filtered[recent_filtered['timestamp'].dt.year == current_year].copy(
        )
        if not current_temp.empty:
            current_temp_data = current_temp.groupby(
                'day_of_year')['current_temperature'].mean().reset_index()
            current_temp_data['type'] = f'{current_year} Temperature'
            current_temp_data['value'] = current_temp_data['current_temperature']
            datasets.append(
                current_temp_data[['day_of_year', 'value', 'type']])

    if not historical_filtered.empty:
        historical_current_year = historical_filtered[historical_filtered['year'] == current_year].copy(
        )
        if not historical_current_year.empty:
            hist_current_temp = historical_current_year.groupby(
                'day_of_year')['hourly_temperature'].mean().reset_index()
            hist_current_temp['type'] = f'{current_year} Temperature'
            hist_current_temp['value'] = hist_current_temp['hourly_temperature']
            datasets.append(
                hist_current_temp[['day_of_year', 'value', 'type']])

    if not historical_filtered.empty:
        baseline_data = historical_filtered[
            (historical_filtered['year'] >= 1940) &
            (historical_filtered['year'] <= 1960)
        ].copy()
        if not baseline_data.empty:
            baseline_temp = baseline_data.groupby(
                'day_of_year')['hourly_temperature'].mean().reset_index()
            baseline_temp['type'] = 'Average 1940-1960'
            baseline_temp['value'] = baseline_temp['hourly_temperature']
            datasets.append(baseline_temp[['day_of_year', 'value', 'type']])

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )
        if not future_2045.empty:
            future_temp = future_2045.groupby(
                'day_of_year')['mean_temperature'].mean().reset_index()
            future_temp['type'] = '2045 Prediction'
            future_temp['value'] = future_temp['mean_temperature']
            datasets.append(future_temp[['day_of_year', 'value', 'type']])

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()


def prepare_rainfall_data(selected_location_id):
    """Prepare rainfall data for visualization"""

    recent_df = load_recent_weather(selected_location_id)
    historical_df = load_past_weather(selected_location_id)
    future_df = load_future_weather(selected_location_id)

    recent_filtered = recent_df[recent_df['location_id']
                                == selected_location_id].copy()
    historical_filtered = historical_df[historical_df['location_id']
                                        == selected_location_id].copy()
    future_filtered = future_df[future_df['location_id']
                                == selected_location_id].copy()

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])
        recent_filtered['day_of_year'] = recent_filtered['timestamp'].dt.dayofyear

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    datasets = []
    current_year = dt.datetime.now().year

    if not recent_filtered.empty:
        current_rain = recent_filtered[recent_filtered['timestamp'].dt.year == current_year].copy(
        )
        if not current_rain.empty:
            current_rain_data = current_rain.groupby(
                'day_of_year')['rainfall_last_15_mins'].sum().reset_index()
            current_rain_data['type'] = f'{current_year} Rainfall'
            current_rain_data['value'] = current_rain_data['rainfall_last_15_mins']
            datasets.append(
                current_rain_data[['day_of_year', 'value', 'type']])

    if not historical_filtered.empty:
        historical_current_year = historical_filtered[historical_filtered['year'] == current_year].copy(
        )
        if not historical_current_year.empty:
            hist_current_rain = historical_current_year.groupby(
                'day_of_year')['hourly_rainfall'].sum().reset_index()
            hist_current_rain['type'] = f'{current_year} Rainfall'
            hist_current_rain['value'] = hist_current_rain['hourly_rainfall']
            datasets.append(
                hist_current_rain[['day_of_year', 'value', 'type']])

        if not historical_filtered.empty:
            baseline_data = historical_filtered[
                (historical_filtered['year'] >= 1940) &
                (historical_filtered['year'] <= 1960)
            ].copy()
            if not baseline_data.empty:
                daily = baseline_data.groupby(['year', 'day_of_year'])[
                    'hourly_rainfall'].sum().reset_index()
                baseline_rain = daily.groupby('day_of_year')[
                    'hourly_rainfall'].mean().reset_index()
                baseline_rain['type'] = 'Average 1940-1960'
                baseline_rain['value'] = baseline_rain['hourly_rainfall']
                datasets.append(
                    baseline_rain[['day_of_year', 'value', 'type']])

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )
        if not future_2045.empty:
            future_rain = future_2045.groupby(
                'day_of_year')['total_rainfall'].sum().reset_index()
            future_rain['type'] = '2045 Prediction'
            future_rain['value'] = future_rain['total_rainfall']
            datasets.append(future_rain[['day_of_year', 'value', 'type']])

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data

    return pd.DataFrame()


def prepare_wind_speed_data(selected_location_id):
    """Prepare wind speed data for visualization"""

    recent_df = load_recent_weather(selected_location_id)
    historical_df = load_past_weather(selected_location_id)
    future_df = load_future_weather(selected_location_id)

    recent_filtered = recent_df[recent_df['location_id']
                                == selected_location_id].copy()
    historical_filtered = historical_df[historical_df['location_id']
                                        == selected_location_id].copy()
    future_filtered = future_df[future_df['location_id']
                                == selected_location_id].copy()

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])
        recent_filtered['day_of_year'] = recent_filtered['timestamp'].dt.dayofyear

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    datasets = []
    current_year = dt.datetime.now().year

    if not recent_filtered.empty:
        current_wind = recent_filtered[recent_filtered['timestamp'].dt.year == current_year].copy(
        )
        if not current_wind.empty:
            current_wind_data = current_wind.groupby(
                'day_of_year')['wind_speed'].mean().reset_index()
            current_wind_data['type'] = f'{current_year} Wind Speed'
            current_wind_data['value'] = current_wind_data['wind_speed']
            datasets.append(
                current_wind_data[['day_of_year', 'value', 'type']])

    if not historical_filtered.empty:
        historical_current_year = historical_filtered[historical_filtered['year'] == current_year].copy(
        )
        if not historical_current_year.empty:
            hist_current_wind = historical_current_year.groupby(
                'day_of_year')['hourly_wind_speed'].mean().reset_index()
            hist_current_wind['type'] = f'{current_year} Wind Speed'
            hist_current_wind['value'] = hist_current_wind['hourly_wind_speed']
            datasets.append(
                hist_current_wind[['day_of_year', 'value', 'type']])

    if not historical_filtered.empty:
        baseline_data = historical_filtered[
            (historical_filtered['year'] >= 1940) &
            (historical_filtered['year'] <= 1960)
        ].copy()
        if not baseline_data.empty:
            baseline_wind = baseline_data.groupby(
                'day_of_year')['hourly_wind_speed'].mean().reset_index()
            baseline_wind['type'] = 'Average 1940-1960'
            baseline_wind['value'] = baseline_wind['hourly_wind_speed']
            datasets.append(baseline_wind[['day_of_year', 'value', 'type']])

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )
        if not future_2045.empty:
            future_wind = future_2045.groupby(
                'day_of_year')['mean_wind_speed'].mean().reset_index()
            future_wind['type'] = '2045 Prediction'
            future_wind['value'] = future_wind['mean_wind_speed']
            datasets.append(future_wind[['day_of_year', 'value', 'type']])

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data

    return pd.DataFrame()


def create_chart(data, title, y_axis_title, color_scheme="category10"):
    """Create an Altair line chart"""
    if data.empty:
        return alt.Chart().mark_text(
            text="No data available for selected location",
            fontSize=16,
            color="gray"
        ).resolve_scale(color="independent")

    chart = alt.Chart(data).mark_line(
        point=True,
        strokeWidth=2
    ).add_selection(
        alt.selection_multi(fields=['type'])
    ).encode(
        x=alt.X('day_of_year:O',
                title='Day of Year',
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y('value:Q',
                title=y_axis_title,
                scale=alt.Scale(zero=False)),
        color=alt.Color('type:N',
                        title='Data Series',
                        scale=alt.Scale(scheme=color_scheme)),
        tooltip=['day_of_year:O', 'value:Q', 'type:N']
    ).properties(
        title=title,
        width=700,
        height=400
    ).resolve_scale(
        color='independent'
    ).interactive()

    return chart


def main():
    """main page"""
    st.set_page_config(
        page_title="Weather Dashboard",
        page_icon="🌦️",
        layout="wide"
    )

    st.title("🌦️ Weather Dashboard")
    st.markdown(
        "Compare current year weather with historical baseline (1940-1960) and future predictions (2045)")

    locations_df = load_locations()

    if locations_df.empty:
        st.error("No locations found in the database")
        return

    location_options = dict(
        zip(locations_df['location_name'], locations_df['location_id']))
    selected_location_name = st.selectbox(
        "Select a location:",
        options=list(location_options.keys())
    )
    selected_location_id = location_options[selected_location_name]

    st.subheader(f"Weather data for: {selected_location_name}")

    current_day = dt.date.today().timetuple().tm_yday
    current_year = dt.date.today().year
    st.subheader("🌡️ Temperature Comparison")
    temp_data = prepare_temperature_data(selected_location_id)
    temp_chart = create_chart(
        temp_data,
        "Temperature Throughout the Year",
        "Temperature (°C)",
        'set1'
    )
    st.altair_chart(temp_chart, use_container_width=True)

    if not temp_data.empty:
        current_temp_avg = temp_data[temp_data['type'].str.contains(
            str(current_year))]['value'].mean()
        baseline_temp_avg = temp_data[(temp_data['type'] == 'Average 1940-1960') & (
            temp_data['day_of_year'] <= current_day)]['value'].mean()
        st.metric(
            "Avg Temperature Difference (Current vs 1940-60)",
            f"{current_temp_avg - baseline_temp_avg:.1f}°C")
    st.subheader("🌧️ Rainfall Comparison")
    rain_data = prepare_rainfall_data(selected_location_id)
    rain_chart = create_chart(
        rain_data,
        "Rainfall Throughout the Year",
        "Rainfall (mm)",
        'set2'
    )
    st.altair_chart(rain_chart, use_container_width=True)
    if not rain_data.empty:
        current_rain = rain_data[rain_data['type'].str.contains(
            str(current_year))]['value'].sum()
        baseline_rain = rain_data[(rain_data['type']
                                  == 'Average 1940-1960') & (
            rain_data['day_of_year'] <= current_day)]['value'].sum()
        if baseline_rain > 0:
            rain_change = (
                (current_rain - baseline_rain) / baseline_rain) * 100
            st.metric(
                "Rainfall Change (Current vs 1940-60)",
                f"{rain_change:.1f}%"
            )
    st.subheader("💨 Wind Speed Comparison")
    wind_data = prepare_wind_speed_data(selected_location_id)
    wind_chart = create_chart(
        wind_data,
        "Wind Speed Throughout the Year",
        "Wind Speed (m/s)",
        'set3'
    ).interactive()
    st.altair_chart(wind_chart, use_container_width=True)
    if not wind_data.empty:
        current_wind = wind_data[wind_data['type'].str.contains(
            str(current_year))]['value'].mean()
        baseline_wind = wind_data[(wind_data['type']
                                  == 'Average 1940-1960') & (
            wind_data['day_of_year'] <= current_day)]['value'].mean()
        wind_diff = current_wind - baseline_wind
        st.metric(
            "Wind Speed Difference (Current vs 1940-60)",
            f"{wind_diff:.1f} m/s"
        )


if __name__ == "__main__":
    navbar()
    main()
