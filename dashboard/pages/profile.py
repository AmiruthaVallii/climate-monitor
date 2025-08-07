# pylint: disable=import-error
"""Profile management page for the dashboard."""
import os
import json
import streamlit as st
import requests as req
import psycopg2
import psycopg2.extras
import pandas as pd
import folium as fl
from streamlit_folium import st_folium
import boto3
from login import get_conn  # pylint: disable=import-error
from modules.nav import navbar

LAMBDA_NAME = "c18-climate-monitor-new-location-orchestrator-lambda"

boto3.setup_default_session(
    aws_access_key_id=os.getenv("MY_AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("MY_AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("MY_AWS_REGION")
)


def logout() -> None:
    """Logout of dashboard."""
    st.session_state["logged_in"] = False
    del st.session_state["user_id"]
    del st.session_state["username"]


def get_users_locations():
    """Get the users locations."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(("SELECT l.location_id, l.location_name, la.subscribe_to_alerts, la.subscribe_to_summary "
                         "FROM locations as l "
                         "JOIN location_assignment AS la USING (location_id) "
                         "JOIN users AS u USING (user_id) "
                         "WHERE u.user_id=%s"),
                        (st.session_state["user_id"],))
            return cur.fetchall()
    finally:
        conn.close()


def get_all_locations():
    """Get all locations stored in the RDS."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(("SELECT * "
                         "FROM locations"))
            data = cur.fetchall()
            return data
    finally:
        conn.close()


def get_location_assignment(user_id: int, location_id: str) -> tuple:
    """Get location assignments."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(("SELECT subscribe_to_alerts, subscribe_to_summary "
                         "FROM location_assignment "
                         "WHERE user_id=%s "
                         "AND location_id=%s;"),
                        (user_id, location_id))
            data = cur.fetchone()
            if data is None:
                data = {"subscribe_to_alerts": False,
                        "subscribe_to_summary": False,
                        "record_exists": False}
            return data
    finally:
        conn.close()


def update_location_assignment(user_id: int, location_id: int, record_exists: bool, get_alerts: bool, get_summary: bool) -> None:
    conn = get_conn()
    try:
        cur = conn.cursor()
        if (not get_alerts) and (not get_summary):
            if not record_exists:
                return None
            cur.execute(("DELETE FROM location_assignment "
                         "WHERE user_id=%s AND location_id=%s;"),
                        (user_id, location_id))
            conn.commit()
            return None
        if record_exists:
            cur.execute(("UPDATE location_assignment "
                         "SET subscribe_to_alerts = %s, "
                         "subscribe_to_summary = %s "
                         "WHERE user_id = %s "
                         "AND location_id = %s;"),
                        (get_alerts, get_summary, user_id, location_id))
            conn.commit()
            return None
        cur.execute(("INSERT INTO location_assignment "
                     "(user_id, location_id, subscribe_to_alerts, subscribe_to_summary) "
                     "VALUES (%s, %s, %s, %s);"),
                    (user_id, location_id, get_alerts, get_summary))
        conn.commit()
    finally:
        conn.close()


def map_get_notifications_callback(user_id: int, location_id: int, record_exists: bool) -> None:
    """Update user location assignments and notification options."""
    get_alerts = st.session_state.get(
        ("get_notifications", "alerts", location_id))
    get_summary = st.session_state.get(
        ("get_notifications", "summary", location_id))
    conn = get_conn()
    update_location_assignment(
        user_id, location_id, record_exists, get_alerts, get_summary)


def insert_new_location(latitude: float, longitude: float) -> None:
    """Insert a new location into the database."""
    location_name = st.session_state.get(
        ("new_location_name", latitude, longitude))
    get_alerts = st.session_state.get(
        ("new_location_alerts", latitude, longitude))
    get_summary = st.session_state.get(
        ("new_location_summary", latitude, longitude))
    if (not location_name) or not (location_name.isalpha()):
        st.write("Error: characters in location name must be alphabetic.")
        return None
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(("INSERT INTO locations (location_name, latitude, longitude) "
                     "VALUES (%s, %s, %s) "
                     "RETURNING location_id;"),
                    (location_name, latitude, longitude))
        location_id = cur.fetchone()[0]
        st.write(location_id)
        conn.commit()
        if get_alerts or get_summary:
            cur.execute(("INSERT INTO location_assignment "
                        "(user_id, location_id, subscribe_to_alerts, subscribe_to_summary) "
                         "VALUES (%s, %s, %s, %s);"),
                        (st.session_state.user_id, location_id, get_alerts, get_summary))
            conn.commit()
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="Event",
            Payload=json.dumps({"location_id": location_id,
                                "latitude": latitude,
                                "longitude": longitude})
        )
    except psycopg2.errors.UniqueViolation:
        st.write("Error: location name already exists, pick a new one.")
    finally:
        conn.close()


def notification_manager_callback(location: dict):
    get_alerts = st.session_state.get(
        ("notification_manage_form", location["location_id"]))
    get_summary = st.session_state.get(
        ("notification_manager_form", location["location_id"])
    )
    update_location_assignment(
        st.session_state.user_id, location["location_id"], True, get_alerts, get_summary)


def notification_manager_form(location: dict) -> None:
    with st.form(location["location_name"],
                 enter_to_submit=False,
                 border=False):
        col1, col2, col3, col4 = st.columns((1, 1, 1, 1))
        with col1:
            st.write(location["location_name"])
        with col2:
            alerts = st.checkbox(
                "Alerts", value=location["subscribe_to_alerts"],
                key=("notification_manage_form", location["location_id"]))
        with col3:
            summary = st.checkbox(
                "Summary", value=location["subscribe_to_summary"],
                key=("notification_manager_form", location["location_id"]))
        with col4:
            submitted = st.form_submit_button(
                "Submit", on_click=notification_manager_callback, args=(location,))


if __name__ == "__main__":
    if not st.session_state.get("logged_in"):
        st.switch_page("login.py")
    navbar()
    st.set_page_config(
        page_title="My Profile",
        page_icon="👤",
        layout="wide"
    )
    st.title("👤 My Profile")
    locations = get_all_locations()
    if "user_id" not in st.session_state and st.session_state.get("logged_in"):
        my_conn = get_conn()
        try:
            with my_conn.cursor() as my_cur:
                my_cur.execute("SELECT user_id FROM users WHERE username= %s",
                               (st.session_state["username"],))
                user_data = my_cur.fetchone()
            st.session_state["user_id"] = user_data[0]
        finally:
            my_conn.close()
    if not st.session_state.get("logged_in"):
        st.page_link("login.py", label="Please login", icon="🔐")

    else:
        st.write("You are logged in!")
        st.button("Logout", on_click=logout)
        st.header("Manage notifications")
        my_locations = get_users_locations()
        if not my_locations:
            st.text("You have no locations, add some below!")
        else:
            for subscribed_location in my_locations:
                notification_manager_form(subscribed_location)
        st.header("Add a location")
        col1, col2 = st.columns([3, 2])
        location_id_map = {}
        with col1:
            my_map = fl.Map(location=[55.5, -4], zoom_start=4.6, max_bounds=True,
                            min_lat=-90, max_lat=90, min_lon=-180, max_lon=180)
            my_map.add_child(fl.LatLngPopup())
            for location in locations:
                fl.Marker(
                    location=[location["latitude"], location["longitude"]],
                    popup=fl.Popup(
                        location["location_name"], parse_html=False),
                    tooltip=location["location_name"]
                ).add_to(my_map)
                location_id_map[location["location_name"]
                                ] = location["location_id"]
            out = st_folium(my_map)
        with col2:
            with st.container(height=330):
                st.subheader("Get notifications")
                if out.get("last_object_clicked_popup"):
                    with st.form("existing_location",
                                 enter_to_submit=False,
                                 border=True,
                                 height='stretch'):
                        la = get_location_assignment(
                            st.session_state["user_id"],
                            location_id_map[out["last_object_clicked_popup"]]
                        )
                        st.subheader(out["last_object_clicked_popup"])
                        alerts = st.checkbox(
                            "Alerts", value=la["subscribe_to_alerts"],
                            key=("get_notifications", "alerts",
                                 location_id_map[out["last_object_clicked_popup"]])
                        )
                        summary = st.checkbox(
                            "Summary", value=la["subscribe_to_summary"],
                            key=("get_notifications", "summary",
                                 location_id_map[out["last_object_clicked_popup"]])
                        )
                        submitted = st.form_submit_button(
                            "Submit", on_click=map_get_notifications_callback,
                            args=(st.session_state["user_id"],
                                  location_id_map[out["last_object_clicked_popup"]],
                                  la.get("record_exists", True)))
                        if submitted:
                            st.write("Submitted")
                        # la = get_location_assignment(
                        #     st.session_state["user_id"],
                        #     location_id_map[out["last_object_clicked_popup"]]
                        # )
                        # st.subheader(out["last_object_clicked_popup"])
                        # alerts = st.checkbox(
                        #     "Alerts", value=la["subscribe_to_alerts"],
                        # )
                        # summary = st.checkbox(
                        #     "Summary", value=la["subscribe_to_summary"],
                        # )
                        # submitted = st.form_submit_button(
                        #     "Submit")
                        # if submitted:
                        #     update_location_assignment(
                        #         st.session_state.user_id, location_id_map[out["last_object_clicked_popup"]], la.get("record_exists", True), alerts, summary)
                        #     st.write("Submitted")
                else:
                    st.write("Click on a pin")
            with st.container(height=340):
                st.subheader("Add new location")
                if out.get("last_clicked"):
                    lat, lon = out["last_clicked"]["lat"], out["last_clicked"]["lng"]
                    with st.form("new_location",
                                 enter_to_submit=False,
                                 border=True,
                                 height='stretch'):
                        st.text(f"Coordinates: {lat:.2f}°N, {lon:.2f}°E")
                        name = st.text_input(
                            "Location name:", placeholder="Enter location name", label_visibility="collapsed",
                            key=("new_location_name", lat, lon))
                        alerts = st.checkbox(
                            "Alerts", key=("new_location_alerts", lat, lon))
                        summary = st.checkbox(
                            "Summary", key=("new_location_summary", lat, lon))
                        submitted = st.form_submit_button(
                            "Submit", on_click=insert_new_location, args=(lat, lon))
                        if submitted:
                            # insert_new_location(
                            #     name, lat, lon, alerts, summary)
                            st.write("Submitted")
