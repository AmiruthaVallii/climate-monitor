"""Air quality page of the climate monitor dashboard"""

import os
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

import pandas as pd
import streamlit as st
import psycopg2
from dotenv import load_dotenv
import altair as alt


load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

HISTORIC_DATA_START_DATE = date(2020, 11, 27)


def get_connection() -> psycopg2.extensions.connection:
    """Returns connection to RDS."""
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


@st.cache_data
def get_locations() -> pd.DataFrame:
    """Returns all locations"""
    with get_connection() as conn:
        logging.info("Connected to database.")
        query = """
            SELECT location_id, location_name
            FROM locations;
        """
    return pd.read_sql_query(query, conn)


@st.cache_data
def get_historical_readings(location_id: int) -> pd.DataFrame:
    """Returns all historical air quality data for a given location"""
    with get_connection() as conn:
        logging.info("Connected to database.")
        query = f"""
            SELECT
                timestamp,
                hourly_air_quality_index AS air_quality_index,
                hourly_carbon_monoxide AS carbon_monoxide,
                hourly_nitrogen_dioxide AS nitrogen_dioxide,
                hourly_nitrogen_monoxide AS nitrogen_monoxide,
                hourly_ammonia AS ammonia,
                hourly_ozone AS ozone,
                hourly_sulphur_dioxide AS sulphur_dioxide,
                hourly_pm2_5 AS pm2_5,
                hourly_pm10 AS pm10
            FROM historical_air_quality
            WHERE location_id = {location_id};
        """
    return pd.read_sql_query(query, conn)


@st.cache_data(ttl=900)
def get_live_readings(location_id: int) -> pd.DataFrame:
    """Returns all live air quality data for a given location"""
    with get_connection() as conn:
        logging.info("Connected to database.")
        query = """
            SELECT
                timestamp,
                air_quality_index,
                carbon_monoxide,
                nitrogen_dioxide,
                nitrogen_monoxide,
                ammonia,
                ozone,
                sulphur_dioxide,
                pm2_5,
                pm10
            FROM air_quality_readings
            WHERE location_id = %s;
        """
    return pd.read_sql_query(query, conn, params=(location_id,))


def locations_sidebar(locations_df: pd.DataFrame) -> tuple[int, str]:
    """Create a locations sidebar and return the chosen location"""

    # location_names = locations["location_name"]
    with st.sidebar:
        choice = st.selectbox(
            "Choose a location:",
            locations_df["location_name"]
        )

    location_id = locations_df[(
        locations_df["location_name"] == choice)]["location_id"].item()

    return location_id, choice


def live_data_metrics(df: pd.DataFrame):
    """Display the most recent air quality metrics on the dashboard"""
    st.header("Latest Air Quality Metrics (μg/m\u2083)")
    last = df.iloc[-1]
    second_last = df.iloc[-5]

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Air Quality Index", last["air_quality_index"],
                int(second_last["air_quality_index"] -
                    last["air_quality_index"]), border=True, delta_color="inverse")
    col2.metric("Carbon Monoxide - CO", last["carbon_monoxide"],
                round(float(second_last["carbon_monoxide"] -
                      last["carbon_monoxide"]), 2),
                border=True, delta_color="inverse")
    col3.metric("Nitrogen Monoxide - NO", last["nitrogen_monoxide"],
                round(float(second_last["nitrogen_monoxide"] -
                      last["nitrogen_monoxide"]), 2),
                border=True, delta_color="inverse")
    col4.metric("Nitrogen Dioxide - NO\u2082", last["nitrogen_dioxide"],
                round(float(second_last["nitrogen_dioxide"] -
                      last["nitrogen_dioxide"]), 2),
                border=True, delta_color="inverse")
    col5.metric("Ammonia - NH\u2083", last["ammonia"],
                round(float(second_last["ammonia"] -
                      last["ammonia"]), 2),
                border=True, delta_color="inverse")
    col2.metric("Ozone - O\u2083", last["ozone"],
                round(float(second_last["ozone"] - last["ozone"]), 2),
                border=True, delta_color="inverse")
    col3.metric("Sulphur Dioxide - SO\u2082", last["sulphur_dioxide"],
                round(float(second_last["sulphur_dioxide"] -
                      last["sulphur_dioxide"]), 2),
                border=True, delta_color="inverse")
    col4.metric("Fine Particulates - PM\u2082.\u2085", last["pm2_5"],
                round(float(second_last["pm2_5"] - last["pm2_5"]), 2),
                border=True, delta_color="inverse")
    col5.metric("Coarse Particulates - PM\u2081\u2080", last["pm10"],
                round(float(second_last["pm10"] - last["pm10"]), 2),
                border=True, delta_color="inverse")


def readings_select() -> list:
    """Streamlit multiselect widget to choose which pollutant you want to filter by"""
    options = st.multiselect(
        "Choose pollutants to filter by:",
        ["Carbon monoxide", "Nitrogen monoxide", "Nitrogen dioxide",
            "Ozone", "Sulphur dioxide", "Ammonia", "PM\u2082.\u2085", "PM\u2081\u2080"],
        default=["Carbon monoxide"],
    )
    name_mapping = {
        "Carbon monoxide": "carbon_monoxide",
        "Nitrogen monoxide": "nitrogen_monoxide",
        "Nitrogen dioxide": "nitrogen_dioxide",
        "Ozone": "ozone",
        "Sulphur dioxide": "sulphur_dioxide",
        "Ammonia": "ammonia",
        "PM\u2082.\u2085": "pm2_5",
        "PM\u2081\u2080": "pm10"
    }
    return [name_mapping.get(name) for name in options]


def date_select(graph_key: str) -> tuple:
    """Retrieve a date period from the user"""
    return st.date_input(
        "Choose a date period:",
        (date.today() - relativedelta(years=1), date.today()),
        min_value=HISTORIC_DATA_START_DATE,
        max_value=date.today() + relativedelta(days=1),
        format="DD/MM/YYYY",
        key=graph_key
    )


def time_group(graph_key: str) -> str:
    """Use Streamlit Pills to allow the user to choose a time period to group by"""
    options = ["Hour", "Day", "Week", "Month", "Year"]
    selection = st.pills("Time period to group readings by:",
                         options,
                         default="Day",
                         selection_mode="single",
                         key=graph_key)

    time_period_map = {
        "Hour": "h",
        "Day": "D",
        "Week": "W",
        "Month": "MS",
        "Year": "YS"
    }
    return time_period_map.get(selection)


def aqi_line_graph(df: pd.DataFrame) -> None:
    """Create a line graph to show the max AQI per day over time"""

    dates = date_select("aqi_line_graph_date")
    if len(dates) != 2:
        st.stop()
    start_date, end_date = dates

    df = df[(df["timestamp"] >= pd.to_datetime(start_date)) & (
        df["timestamp"] <= pd.to_datetime(end_date))]

    time_period = time_group("aqi_line_graph_time_period")

    df = df.groupby(
        pd.Grouper(key="timestamp", freq=time_period))["air_quality_index"].max().reset_index()

    st.altair_chart(
        alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title="Date"),
            y=alt.Y("air_quality_index:Q", title="Air Quality Index",
                    scale=alt.Scale(domain=[1, 5])),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Date"),
                alt.Tooltip("air_quality_index:Q", title="Air Quality Index")
            ]
        ).properties(
            width=1000,
            height=400
        )
    )


def all_time_readings_line_graph(df: pd.DataFrame) -> None:
    """Create a line graph to show the max pollutant readings per day over time"""

    dates = date_select("pollutant_line_graph")
    if len(dates) != 2:
        st.stop()
    start_date, end_date = dates

    df = df[(df["timestamp"] >= pd.to_datetime(start_date)) & (
        df["timestamp"] <= pd.to_datetime(end_date))]

    time_period = time_group("pollutant_line_graph_time_period")

    df = df.groupby(
        pd.Grouper(key="timestamp", freq=time_period)).mean().reset_index()
    long_df = df.melt(id_vars=["timestamp"],
                      var_name="pollutant", value_name="value")

    st.altair_chart(
        alt.Chart(long_df).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title="Date"),
            y=alt.Y("value:Q", title="Mean Value per Day (μg/m\u2083)"),
            color=alt.Color("pollutant:N", title="Pollutant"),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Date"),
                alt.Tooltip(
                    "value:Q", title="Mean Value per Day (μg/m\u2083)"),
                alt.Tooltip("pollutant:N", title="Pollutant")
            ]
        ).properties(
            width=1000,
            height=500
        )
    )


if __name__ == "__main__":

    st.set_page_config(
        page_title="Air Quality Intel",
        page_icon="😷",
        layout="wide"
    )

    locations = get_locations()
    chosen_location_id, location_name = locations_sidebar(locations)

    st.title(f"😷 Air Quality in {location_name}")
    st.divider()
    st.markdown("####")

    historical_data = get_historical_readings(chosen_location_id)
    live_data = get_live_readings(chosen_location_id)
    all_data = pd.concat([historical_data, live_data])
    live_data_metrics(all_data)
    st.markdown("####")

    st.header("Readings over Time")
    st.subheader("Air Quality Index Readings")
    aqi_line_graph(all_data)

    st.markdown("#####")
    st.subheader("Pollutants Readings")
    pollutants = readings_select()
    columns = ["timestamp"] + pollutants
    all_time_readings_line_graph(all_data[columns])
