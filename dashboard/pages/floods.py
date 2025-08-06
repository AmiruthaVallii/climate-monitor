"""Fetches flood information from RDS and renders flood page for dashboard"""
import os
import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import altair as alt


def get_conn():
    """Returns connection to RDS."""

    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


def get_live_flood_warnings() -> pd.DataFrame:
    """Fetches live flood warnings from the database."""

    try:
        with get_conn() as conn:

            query = """
                SELECT 
                    fw.updated_at, 
                    l.location_name AS location, 
                    fs.severity_name, 
                    fw.location_description, 
                    fw.message
                FROM flood_warnings fw
                JOIN flood_areas fa ON fw.flood_area_id = fa.flood_area_id
                JOIN flood_area_assignment faa ON fa.flood_area_id = faa.flood_area_id
                JOIN locations l ON faa.location_id = l.location_id
                JOIN flood_severity fs ON fw.severity_id = fs.severity_id
                ORDER BY fw.updated_at DESC;
            """
            return pd.read_sql(query, conn)

    except Exception as e:
        st.error(f"Database error loading live warnings: {e}")


def format_text(text):
    """Replaces \n with <br> for HTML formatting."""

    if pd.isna(text):
        return ""
    return str(text).replace("\n", "<br>").replace("\r", "")


def display_live_flood_warnings(live_warnings: pd.DataFrame):
    """Displays live flood warnings."""

    if live_warnings.empty:
        st.success("✅ No active flood warnings.")
    else:
        live_warnings["formatted_time"] = live_warnings["updated_at"].dt.strftime(
            '%Y-%m-%d %H:%M')

        live_warnings["location_description"] = live_warnings["location_description"].apply(
            format_text)
        live_warnings["message"] = live_warnings["message"].apply(format_text)

        st.markdown("""
            <style>
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.5); opacity: 0.5; }
                100% { transform: scale(1); opacity: 1; }
            }
            </style>
        """, unsafe_allow_html=True)

        # iterrows is fine here since there won't be a lot of flood warnings to display at once
        for _, row in live_warnings.iterrows():
            warning_html = f"""
                <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin-bottom:10px;">
                    <div style="display:flex; align-items:center;">
                        <div style="height:10px;width:10px;background:red;border-radius:50%;margin-right:10px;animation:pulse 1s infinite;"></div>
                        <strong>{row['severity_name']}</strong> : {row['location']}
                    </div>
                    <small>{row['formatted_time']}</small><br>
                    <em>{row['location_description']}</em>
                    <p>{row['message']}</p>
                </div>
            """
            st.markdown(warning_html, unsafe_allow_html=True)


def get_historical_flood_data() -> pd.DataFrame:
    """Fetches historical flood data from database."""

    try:
        with get_conn() as conn:
            location_query = """
                SELECT 
                    hf.date, 
                    l.location_name AS location, 
                    fs.severity_name
                FROM historical_floods hf
                JOIN flood_areas fa ON hf.flood_area_id = fa.flood_area_id
                JOIN flood_area_assignment faa ON fa.flood_area_id = faa.flood_area_id
                JOIN locations l ON faa.location_id = l.location_id
                JOIN flood_severity fs ON hf.severity_id = fs.severity_id
                ORDER BY hf.date DESC;
                """
            areas_df = pd.read_sql(location_query, conn)
            return areas_df
    except Exception as e:
        st.error(f"Database error loading historical data: {e}")


def display_historical_flood_data(historical_floods: pd.DataFrame):
    """Displays historical flood data as a line graph.
        - Allows users to select which location they want to view
          data for."""
    if historical_floods.empty:
        st.info("No historical flood data available.")
        return

    location_choices = sorted(historical_floods['location'].unique())
    selected_location = st.selectbox("📍 Select Location", location_choices)

    filtered_df = historical_floods[historical_floods["location"]
                                    == selected_location].copy()
    filtered_df["date"] = pd.to_datetime(filtered_df["date"])

    # group by month and severity
    filtered_df["year"] = filtered_df["date"].dt.to_period(
        "Y").dt.to_timestamp()
    monthly_counts = (
        filtered_df.groupby(["year", "severity_name"])
        .size()
        .reset_index(name="count")
        .rename(columns={"severity_name": "Severity", "year": "Year"})
    )

    chart = alt.Chart(monthly_counts).mark_line(point=True).encode(
        x=alt.X("Year:T", title="Year"),
        y=alt.Y("count:Q", title="Number of Flood Events"),
        color=alt.Color("Severity:N", title="Severity"),
        tooltip=["Year:T", "Severity:N", "count"]
    ).properties(
        width="container",
        height=500,
        title=f"Flood Warnings in {selected_location} Over the Years"
    )

    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":

    load_dotenv()

    st.set_page_config(
        page_title="Flood Intel",
        page_icon="💧",
        layout="wide"
    )

    st.header("🔴 Live Flood Warnings")
    flood_warnings = get_live_flood_warnings()
    display_live_flood_warnings(flood_warnings)

    st.header("📜 Browse Historical Flood Data")
    historical_floods = get_historical_flood_data()
    display_historical_flood_data(historical_floods)
