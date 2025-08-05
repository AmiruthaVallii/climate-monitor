import os
import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime


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


def display_live_flood_warnings(live_warnings: pd.DataFrame):

    if live_warnings.empty:
        st.success("✅ No active flood warnings.")

    else:
        live_warnings["formatted_time"] = live_warnings["updated_at"].dt.strftime(
            '%Y-%m-%d %H:%M')

        live_warnings["html_block"] = live_warnings.apply(lambda row: f"""
            <div style="border:1px solid #ccc; border-radius:10px; padding:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center;">
                    <div style="height:10px;width:10px;background:red;border-radius:50%;margin-right:10px;animation:pulse 1s infinite;"></div>
                    <strong>{row['severity_name']}</strong> — {row['location']}
                </div>
                <small>{row['formatted_time']}</small><br>
                <em>{row['location_description']}</em>
                <p>{row['message']}</p>
            </div>
        """, axis=1)

        combined_html = "\n".join(live_warnings["html_block"])

        combined_html += """
        <style>
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.5); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
        """

        st.markdown(combined_html, unsafe_allow_html=True)


def get_historical_flood_data():
    pass


def display_historical_flood_data():
    pass


if __name__ == "__main__":

    load_dotenv()

    st.set_page_config(
        page_title="Flood Intel",
        page_icon="💧",
    )

    st.title("🌊 Flood Warnings and History")

    st.header("🔴 Live Flood Warnings")

    flood_warnings = get_live_flood_warnings()

    display_live_flood_warnings(flood_warnings)

    st.header("📜 Browse Historical Flood Data")
