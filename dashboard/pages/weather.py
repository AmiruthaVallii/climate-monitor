"""Weather page"""
import streamlit as st
import altair as alt
from dotenv import load_dotenv
import psycopg2
import os
import pandas as pd
import datetime as dt


def get_connection():
    """get rds connection"""
    load_dotenv()
    conn = psycopg2.connect(
        host=os.environ["HOST"],
        user=os.environ["USERNAME"],
        password=os.environ["DBPASSWORD"],
        dbname=os.environ["DBNAME"],
        port=5432)
    return conn


@st.cache_data(ttl='300')
def load_recent_weather():
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = 'select * from weather_readings;'
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
    return df


@st.cache_data()
def load_past_weather():
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = 'select * from historical_weather_readings;'
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
    return df


@st.cache_data()
def load_future_weather():
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = 'select * from future_weather_prediction;'
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()
    return df


def current_temp(selected_locations):
    df = load_recent_weather()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    st.title(" Temperature Over Time by Location")
    filtered_df = df[df["location_id"].isin(selected_locations)]

    chart = (
        alt.Chart(filtered_df)
        .mark_line()
        .encode(
            x=alt.X("timestamp:T", title="Time"),
            y=alt.Y("current_temperature:Q", title="Temperature (°C)"),
            color=alt.Color("location_id:N", title="Location"),
            tooltip=["timestamp:T", "location_id:N", "current_temperature:Q"]
        )
        .properties(width=700, height=400)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def current_rain():
    df = load_recent_weather()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df['date'] = df['timestamp'].dt.date
    daily_rain = df.groupby(['location_id', 'date'])['rainfall_last_15_mins'].sum(
    ).reset_index().rename(columns={'rainfall_last_15_mins': 'daily_rainfall'})
    st.title("Daily rainfall over time by location")
    locations = daily_rain["location_id"].unique()
    selected_locations = st.multiselect(
        "Select locations", options=locations, default=list(locations))
    filtered_df = daily_rain[daily_rain["location_id"].isin(
        selected_locations)]

    chart = (
        alt.Chart(filtered_df)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Time"),
            y=alt.Y("daily_rainfall:Q", title="daily_rainfall (mm)"),
            color=alt.Color("location_id:N", title="Location"),
            tooltip=["date:T", "location_id:N", "daily_rainfall:Q"]
        )
        .properties(width=700, height=400)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def current_wind(selected_locations):
    df = load_recent_weather()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    st.title(" wind speed Over Time by Location")

    filtered_df = df[df["location_id"].isin(selected_locations)]

    chart = (
        alt.Chart(filtered_df)
        .mark_line()
        .encode(
            x=alt.X("timestamp:T", title="Time"),
            y=alt.Y("wind_speed:Q", title="wind_speed"),
            color=alt.Color("location_id:N", title="Location"),
            tooltip=["timestamp:T", "location_id:N", "wind_speed:Q"]
        )
        .properties(width=700, height=400)
        .interactive()
    )
    historical_df = load_past_weather()

    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    st.title('Weather page')
    df = load_recent_weather()
    locations = df["location_id"].unique()
    selected_locations = st.multiselect(
        "Select locations", options=locations, default=list(locations))
    current_temp(selected_locations)
    current_rain()
    current_wind(selected_locations)
