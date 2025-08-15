# pylint: disable=import-error
"""Weather Dashboard"""
import os
import datetime as dt
import pandas as pd
from dateutil.relativedelta import relativedelta

import psycopg2
from dotenv import load_dotenv
import altair as alt
import streamlit as st
from modules.nav import navbar
HISTORIC_DATA_START_DATE = dt.date(2020, 1, 1)


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
def load_past_weather(location_id, start_year=None, end_year=None):
    """loads past weather from rds"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if start_year and end_year:
            query = """select * from historical_weather_readings WHERE location_id = %s
            AND (EXTRACT(YEAR FROM timestamp) BETWEEN 1940 AND 1960 
            OR EXTRACT(YEAR FROM timestamp) BETWEEN %s AND %s);"""
            parameters = (location_id, start_year, end_year)
        else:
            query = """select * from historical_weather_readings WHERE location_id = %s
            AND EXTRACT(YEAR FROM timestamp) BETWEEN 1940 AND 1960;"""
            parameters = (location_id,)

        cur.execute(query, parameters)
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
        query = "select * from future_weather_prediction WHERE location_id = %s AND EXTRACT(YEAR FROM date)=2045"
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


def prepare_temperature_data(selected_location_id: int, date_range: tuple) -> pd.DataFrame:
    """Prepare temperature data for visualization with selected date range"""

    start_date, end_date = date_range
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    start_year = start_date.year
    end_year = end_date.year

    recent_filtered = load_recent_weather(selected_location_id)
    historical_filtered = load_past_weather(
        selected_location_id, start_year, end_year)
    future_filtered = load_future_weather(selected_location_id)

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    date_range_df = pd.DataFrame({
        'date': pd.date_range(start=start_date, end=end_date, freq='D')
    })
    date_range_df['day_of_year'] = date_range_df['date'].dt.dayofyear
    date_range_df['year'] = date_range_df['date'].dt.year

    datasets = []

    all_selected_data = []

    if not recent_filtered.empty:
        recent_in_range = recent_filtered[
            (recent_filtered['timestamp'] >= start_date) &
            (recent_filtered['timestamp'] <= end_date)
        ].copy()

        if not recent_in_range.empty:
            recent_daily = recent_in_range.groupby(
                recent_in_range['timestamp'].dt.date
            )['current_temperature'].mean().reset_index()
            recent_daily.columns = ['date', 'temperature']
            recent_daily['date'] = pd.to_datetime(recent_daily['date'])
            all_selected_data.append(recent_daily)

    if not historical_filtered.empty:
        historical_in_range = historical_filtered[
            (historical_filtered['timestamp'] >= start_date) &
            (historical_filtered['timestamp'] <= end_date)
        ].copy()

        if not historical_in_range.empty:
            hist_daily = historical_in_range.groupby(
                historical_in_range['timestamp'].dt.date
            )['hourly_temperature'].mean().reset_index()
            hist_daily.columns = ['date', 'temperature']
            hist_daily['date'] = pd.to_datetime(hist_daily['date'])
            all_selected_data.append(hist_daily)

    if all_selected_data:
        combined_selected = pd.concat(all_selected_data, ignore_index=True)
        combined_selected = combined_selected.groupby(
            'date')['temperature'].mean().reset_index()
        combined_selected['type'] = 'Selected Period'
        combined_selected['value'] = combined_selected['temperature']
        datasets.append(combined_selected[['date', 'value', 'type']])

    if not historical_filtered.empty:
        baseline_data = historical_filtered[
            (historical_filtered['year'] >= 1940) &
            (historical_filtered['year'] <= 1960)
        ].copy()

        if not baseline_data.empty:
            baseline_temp = baseline_data.groupby(
                'day_of_year')['hourly_temperature'].mean().reset_index()
            baseline_temp.rename(
                columns={'hourly_temperature': 'baseline_value'}, inplace=True)

            baseline_mapped = date_range_df.merge(
                baseline_temp, on='day_of_year', how='left')
            baseline_mapped['type'] = 'Average 1940-1960'
            baseline_mapped['value'] = baseline_mapped['baseline_value']
            baseline_mapped = baseline_mapped[[
                'date', 'value', 'type']].dropna()
            datasets.append(baseline_mapped)

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )

        if not future_2045.empty:
            future_temp = future_2045.groupby(
                'day_of_year')['mean_temperature'].mean().reset_index()
            future_temp.rename(
                columns={'mean_temperature': 'future_value'}, inplace=True)

            future_mapped = date_range_df.merge(
                future_temp, on='day_of_year', how='left')
            future_mapped['type'] = '2045 Prediction'
            future_mapped['value'] = future_mapped['future_value']
            future_mapped = future_mapped[['date', 'value', 'type']].dropna()
            datasets.append(future_mapped)

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()


def prepare_rainfall_data(selected_location_id: int, date_range: tuple) -> pd.DataFrame:
    """Prepare rainfall data for visualization with selected date range"""

    start_date, end_date = date_range
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    start_year = start_date.year
    end_year = end_date.year

    recent_filtered = load_recent_weather(selected_location_id)
    historical_filtered = load_past_weather(
        selected_location_id, start_year, end_year)
    future_filtered = load_future_weather(selected_location_id)

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    date_range_df = pd.DataFrame({
        'date': pd.date_range(start=start_date, end=end_date, freq='D')
    })
    date_range_df['day_of_year'] = date_range_df['date'].dt.dayofyear
    date_range_df['year'] = date_range_df['date'].dt.year

    datasets = []

    all_selected_data = []

    if not recent_filtered.empty:
        recent_in_range = recent_filtered[
            (recent_filtered['timestamp'] >= start_date) &
            (recent_filtered['timestamp'] <= end_date)
        ].copy()

        if not recent_in_range.empty:
            recent_daily = recent_in_range.groupby(
                recent_in_range['timestamp'].dt.date
            )['rainfall_last_15_mins'].sum().reset_index()
            recent_daily.columns = ['date', 'rainfall']
            recent_daily['date'] = pd.to_datetime(recent_daily['date'])
            all_selected_data.append(recent_daily)

    if not historical_filtered.empty:
        historical_in_range = historical_filtered[
            (historical_filtered['timestamp'] >= start_date) &
            (historical_filtered['timestamp'] <= end_date)].copy()

        if not historical_in_range.empty:
            hist_daily = historical_in_range.groupby(
                historical_in_range['timestamp'].dt.date
            )['hourly_rainfall'].sum().reset_index()
            hist_daily.columns = ['date', 'rainfall']
            hist_daily['date'] = pd.to_datetime(hist_daily['date'])
            all_selected_data.append(hist_daily)

    if all_selected_data:
        combined_selected = pd.concat(all_selected_data, ignore_index=True)
        combined_selected = combined_selected.groupby(
            'date')['rainfall'].sum().reset_index()
        combined_selected['type'] = 'Selected Period'
        combined_selected['value'] = combined_selected['rainfall']
        datasets.append(combined_selected[['date', 'value', 'type']])

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
            baseline_rain.rename(
                columns={'hourly_rainfall': 'baseline_value'}, inplace=True)

            baseline_mapped = date_range_df.merge(
                baseline_rain, on='day_of_year', how='left')
            baseline_mapped['type'] = 'Average 1940-1960'
            baseline_mapped['value'] = baseline_mapped['baseline_value']
            baseline_mapped = baseline_mapped[[
                'date', 'value', 'type']].dropna()
            datasets.append(baseline_mapped)

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )

        if not future_2045.empty:
            future_rain = future_2045.groupby(
                'day_of_year')['total_rainfall'].sum().reset_index()
            future_rain.rename(
                columns={'total_rainfall': 'future_value'}, inplace=True)

            future_mapped = date_range_df.merge(
                future_rain, on='day_of_year', how='left')
            future_mapped['type'] = '2045 Prediction'
            future_mapped['value'] = future_mapped['future_value']
            future_mapped = future_mapped[['date', 'value', 'type']].dropna()
            datasets.append(future_mapped)

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data

    return pd.DataFrame()


def prepare_wind_speed_data(selected_location_id: int, date_range: tuple) -> pd.DataFrame:
    """Prepare wind speed data for visualization with selected date range"""

    start_date, end_date = date_range
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    start_year = start_date.year
    end_year = end_date.year

    recent_filtered = load_recent_weather(selected_location_id)
    historical_filtered = load_past_weather(
        selected_location_id, start_year, end_year)
    future_filtered = load_future_weather(selected_location_id)

    if not recent_filtered.empty:
        recent_filtered['timestamp'] = pd.to_datetime(
            recent_filtered['timestamp'])

    if not historical_filtered.empty:
        historical_filtered['timestamp'] = pd.to_datetime(
            historical_filtered['timestamp'])
        historical_filtered['year'] = historical_filtered['timestamp'].dt.year
        historical_filtered['day_of_year'] = historical_filtered['timestamp'].dt.dayofyear

    if not future_filtered.empty:
        future_filtered['date'] = pd.to_datetime(future_filtered['date'])
        future_filtered['day_of_year'] = future_filtered['date'].dt.dayofyear

    date_range_df = pd.DataFrame({
        'date': pd.date_range(start=start_date, end=end_date, freq='D')
    })
    date_range_df['day_of_year'] = date_range_df['date'].dt.dayofyear
    date_range_df['year'] = date_range_df['date'].dt.year

    datasets = []

    all_selected_data = []

    if not recent_filtered.empty:
        recent_in_range = recent_filtered[
            (recent_filtered['timestamp'] >= start_date) &
            (recent_filtered['timestamp'] <= end_date)
        ].copy()

        if not recent_in_range.empty:
            recent_daily = recent_in_range.groupby(
                recent_in_range['timestamp'].dt.date
            )['wind_speed'].mean().reset_index()
            recent_daily.columns = ['date', 'wind_speed']
            recent_daily['date'] = pd.to_datetime(recent_daily['date'])
            all_selected_data.append(recent_daily)

    if not historical_filtered.empty:
        historical_in_range = historical_filtered[
            (historical_filtered['timestamp'] >= start_date) &
            (historical_filtered['timestamp'] <= end_date)
        ].copy()

        if not historical_in_range.empty:
            hist_daily = historical_in_range.groupby(
                historical_in_range['timestamp'].dt.date
            )['hourly_wind_speed'].mean().reset_index()
            hist_daily.columns = ['date', 'wind_speed']
            hist_daily['date'] = pd.to_datetime(hist_daily['date'])
            all_selected_data.append(hist_daily)

    if all_selected_data:
        combined_selected = pd.concat(all_selected_data, ignore_index=True)
        combined_selected = combined_selected.groupby(
            'date')['wind_speed'].mean().reset_index()
        combined_selected['type'] = 'Selected Period'
        combined_selected['value'] = combined_selected['wind_speed']
        datasets.append(combined_selected[['date', 'value', 'type']])

    if not historical_filtered.empty:
        baseline_data = historical_filtered[
            (historical_filtered['year'] >= 1940) &
            (historical_filtered['year'] <= 1960)
        ].copy()

        if not baseline_data.empty:
            baseline_wind = baseline_data.groupby(
                'day_of_year')['hourly_wind_speed'].mean().reset_index()
            baseline_wind.rename(
                columns={'hourly_wind_speed': 'baseline_value'}, inplace=True)

            baseline_mapped = date_range_df.merge(
                baseline_wind, on='day_of_year', how='left')
            baseline_mapped['type'] = 'Average 1940-1960'
            baseline_mapped['value'] = baseline_mapped['baseline_value']
            baseline_mapped = baseline_mapped[[
                'date', 'value', 'type']].dropna()
            datasets.append(baseline_mapped)

    if not future_filtered.empty:
        future_2045 = future_filtered[future_filtered['date'].dt.year == 2045].copy(
        )

        if not future_2045.empty:
            future_wind = future_2045.groupby(
                'day_of_year')['mean_wind_speed'].mean().reset_index()
            future_wind.rename(
                columns={'mean_wind_speed': 'future_value'}, inplace=True)

            future_mapped = date_range_df.merge(
                future_wind, on='day_of_year', how='left')
            future_mapped['type'] = '2045 Prediction'
            future_mapped['value'] = future_mapped['future_value']
            future_mapped = future_mapped[['date', 'value', 'type']].dropna()
            datasets.append(future_mapped)

    if datasets:
        combined_data = pd.concat(datasets, ignore_index=True)
        return combined_data

    return pd.DataFrame()


def create_chart(data: pd.DataFrame, title: str, y_axis_title: str, color_scheme: str = "category10"):
    """Create an Altair line chart with date on x-axis"""
    if data.empty:
        return alt.Chart().mark_text(
            text="No data available for selected location",
            fontSize=16,
            color="gray"
        ).resolve_scale(color="independent")

    date_range = data['date'].max() - data['date'].min()
    if date_range.days <= 31:
        x_format = '%b %d'
        x_title = 'Date'
    elif date_range.days <= 365:
        x_format = '%b %d'
        x_title = 'Date'
    else:
        x_format = '%b %Y'
        x_title = 'Date'

    chart = alt.Chart(data).mark_line(
        point=True,
        strokeWidth=2
    ).encode(
        x=alt.X('date:T',
                title=x_title,
                axis=alt.Axis(format=x_format, labelAngle=-45)),
        y=alt.Y('value:Q',
                title=y_axis_title,
                scale=alt.Scale(zero=False)),
        color=alt.Color('type:N',
                        title='Data Series',
                        scale=alt.Scale(scheme=color_scheme)),
        tooltip=[
            alt.Tooltip('date:T', format='%B %d, %Y', title='Date'),
            alt.Tooltip('value:Q', format='.2f', title=y_axis_title),
            alt.Tooltip('type:N', title='Series')
        ]
    ).properties(
        title=title,
        width=700,
        height=400
    ).interactive()

    return chart


def calculate_metrics(data: pd.DataFrame, metric_type: str) -> dict:
    """Calculate proper metrics for comparison using the entire selected period"""
    if data.empty:
        return {}

    selected_data = data[data['type'] == 'Selected Period']
    baseline_data = data[data['type'] == 'Average 1940-1960']

    metrics = {}

    if not selected_data.empty:
        if metric_type == 'rainfall':
            selected_value = selected_data['value'].sum()
            metrics['selected_value'] = selected_value
            metrics['selected_label'] = f"{selected_value:.1f} mm"
        else:
            selected_value = selected_data['value'].mean()
            metrics['selected_value'] = selected_value
            unit = "°C" if metric_type == 'temperature' else "m/s"
            metrics['selected_label'] = f"{selected_value:.1f} {unit}"

    if not baseline_data.empty:
        if metric_type == 'rainfall':
            baseline_value = baseline_data['value'].sum()
            metrics['baseline_value'] = baseline_value
            metrics['baseline_label'] = f"{baseline_value:.1f} mm"
        else:
            baseline_value = baseline_data['value'].mean()
            metrics['baseline_value'] = baseline_value
            unit = "°C" if metric_type == 'temperature' else "m/s"
            metrics['baseline_label'] = f"{baseline_value:.1f} {unit}"

        if 'selected_value' in metrics and metrics['baseline_value'] != 0:
            diff = metrics['selected_value'] - metrics['baseline_value']
            pct_change = (diff / abs(metrics['baseline_value'])) * 100

            if metric_type == 'rainfall':
                metrics['difference_label'] = f"{diff:.1f} mm"
            else:
                unit = "°C" if metric_type == 'temperature' else "m/s"
                metrics['difference_label'] = f"{diff:.1f} {unit}"

            metrics['percentage_change'] = pct_change
            metrics['difference_value'] = diff

    return metrics


def date_select(graph_key: str) -> tuple:
    """Retrieve a date period from the user"""
    return st.date_input(
        "Choose a date period:",
        (dt.date.today() - relativedelta(years=1), dt.date.today()),
        min_value=HISTORIC_DATA_START_DATE,
        max_value=dt.date.today() + relativedelta(days=1),
        format="DD/MM/YYYY",
        key=graph_key
    )


def main():
    """main page"""
    st.set_page_config(
        page_title="Weather Intel",
        page_icon="🌦️",
        layout="wide"
    )

    st.title("🌦️ Weather Dashboard")
    st.divider()

    locations_df = load_locations()

    if locations_df.empty:
        st.error("No locations found in the database")
        return

    location_options = dict(
        zip(locations_df['location_name'], locations_df['location_id']))

    with st.sidebar:
        st.divider()
        selected_location_name = st.selectbox(
            "📍 Select Location:",
            options=list(location_options.keys())
        )

    st.subheader("📅 Date Range Selection")
    date_range = st.date_input(
        "Select period to analyze:",
        value=(dt.date.today() - relativedelta(years=1), dt.date.today()),
        min_value=HISTORIC_DATA_START_DATE,
        max_value=dt.date.today(),
        format="DD/MM/YYYY",
        key="global_date_range"
    )

    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.warning("Please select both start and end dates")
        return

    selected_location_id = location_options[selected_location_name]

    st.header(f"Weather Data for {selected_location_name}")

    start_date, end_date = date_range
    st.info(
        f"📊 Analyzing period: **{start_date.strftime('%B %d, %Y')}** to **{end_date.strftime('%B %d, %Y')}**")

    st.markdown(
        "Compare selected period weather data with historical "
        "baseline (1940-1960) and future predictions (2045). "
        "The baseline and future predictions repeat for each year in your selected range."
    )

    st.subheader("🌡️ Temperature Comparison")
    temp_data = prepare_temperature_data(selected_location_id, date_range)
    temp_chart = create_chart(
        temp_data,
        "Temperature Throughout Selected Period",
        "Temperature (°C)",
        'set1'
    )
    st.altair_chart(temp_chart, use_container_width=True)

    if not temp_data.empty:
        temp_metrics = calculate_metrics(temp_data, 'temperature')

        if 'selected_value' in temp_metrics and 'baseline_value' in temp_metrics:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selected Period Avg",
                          temp_metrics['selected_label'])
            with col2:
                st.metric("Baseline (1940-60) Avg",
                          temp_metrics['baseline_label'])
            with col3:
                if 'difference_value' in temp_metrics:
                    st.metric("Temperature Difference",
                              temp_metrics['difference_label'],
                              delta=f"{temp_metrics['percentage_change']:.1f}%")

    st.subheader("🌧️ Rainfall Comparison")
    rain_data = prepare_rainfall_data(selected_location_id, date_range)
    rain_chart = create_chart(
        rain_data,
        "Rainfall Throughout Selected Period",
        "Rainfall (mm)",
        'set2'
    )
    st.altair_chart(rain_chart, use_container_width=True)

    if not rain_data.empty:
        rain_metrics = calculate_metrics(rain_data, 'rainfall')

        if 'selected_value' in rain_metrics and 'baseline_value' in rain_metrics:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selected Period Total",
                          rain_metrics['selected_label'])
            with col2:
                st.metric("Baseline (1940-60) Total",
                          rain_metrics['baseline_label'])
            with col3:
                if 'difference_value' in rain_metrics:
                    st.metric("Rainfall Change",
                              f"{rain_metrics['percentage_change']:.1f}%",
                              delta=rain_metrics['difference_label'])

    st.subheader("💨 Wind Speed Comparison")
    wind_data = prepare_wind_speed_data(selected_location_id, date_range)
    wind_chart = create_chart(
        wind_data,
        "Wind Speed Throughout Selected Period",
        "Wind Speed (m/s)",
        'set3'
    )
    st.altair_chart(wind_chart, use_container_width=True)

    if not wind_data.empty:
        wind_metrics = calculate_metrics(wind_data, 'wind_speed')

        if 'selected_value' in wind_metrics and 'baseline_value' in wind_metrics:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Selected Period Avg",
                          wind_metrics['selected_label'])
            with col2:
                st.metric("Baseline (1940-60) Avg",
                          wind_metrics['baseline_label'])
            with col3:
                if 'difference_value' in wind_metrics:
                    st.metric("Wind Speed Difference",
                              wind_metrics['difference_label'],
                              delta=f"{wind_metrics['percentage_change']:.1f}%")


if __name__ == "__main__":
    navbar()
    main()
