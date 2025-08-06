"""Profile management page for the dashboard."""
import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
import folium as fl
from streamlit_folium import st_folium
from login import get_conn  # pylint: disable=import-error


def logout() -> None:
    st.session_state["logged_in"] = False
    del st.session_state["user_id"]
    del st.session_state["username"]


def get_users_locations():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(("SELECT l.location_name, la.subscribe_to_alerts, la.subscribe_to_summary "
                         "FROM locations as l "
                         "JOIN location_assignment AS la USING (location_id) "
                         "JOIN users AS u USING (user_id) "
                         "WHERE u.user_id=%s"),
                        (st.session_state["user_id"],))
            return pd.DataFrame(cur.fetchall())
    finally:
        conn.close()


@st.cache_data(ttl="10m")
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


def update_location_assignment(user_id: int, location_id: int, record_exists: bool) -> None:
    """Update user location assignments and notification options."""
    get_alerts = st.session_state.get(
        ("get_notifications", "alerts", location_id))
    get_summary = st.session_state.get(
        ("get_notifications", "summary", location_id))
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


if __name__ == "__main__":
    st.set_page_config(
        page_title="My Profile",
        page_icon=".streamlit/favicon.png"
    )
    st.title("My Profile")
    locations = get_all_locations()
    if "user_id" not in st.session_state and st.session_state.get("logged_in"):
        my_conn = get_conn()
        try:
            with my_conn.cursor() as my_cur:
                my_cur.execute("SELECT user_id FROM users WHERE username= %s",
                               (st.session_state["username"],))
                data = my_cur.fetchone()
            st.session_state["user_id"] = data[0]
        finally:
            my_conn.close()
    if not st.session_state.get("logged_in"):
        st.page_link("login.py", label="Please login", icon="🔐")

    else:
        st.write("You are logged in!")
        st.button("Logout", on_click=logout)
        st.header("My locations")
        my_locations = get_users_locations()
        if my_locations.empty:
            st.text("You have no locations, add some below!")
        else:
            st.table(my_locations)
        st.header("Add a location")
        col1, col2 = st.columns([3, 2])
        location_id = {}
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
                location_id[location["location_name"]
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
                            location_id[out["last_object_clicked_popup"]]
                        )
                        st.subheader(out["last_object_clicked_popup"])
                        alerts = st.checkbox(
                            "Alerts", value=la["subscribe_to_alerts"],
                            key=("get_notifications", "alerts",
                                 location_id[out["last_object_clicked_popup"]])
                        )
                        summary = st.checkbox(
                            "Summary", value=la["subscribe_to_summary"],
                            key=("get_notifications", "summary",
                                 location_id[out["last_object_clicked_popup"]])
                        )
                        submitted = st.form_submit_button(
                            "Submit", on_click=update_location_assignment,
                            args=(st.session_state["user_id"],
                                  location_id[out["last_object_clicked_popup"]],
                                  la.get("record_exists", True)))
                        if submitted:
                            st.write("Submitted")
                else:
                    st.write("Click on a pin")
            with st.container(height=330):
                st.subheader("Add new location")
                if out.get("last_clicked"):
                    lat, lon = out["last_clicked"]["lat"], out["last_clicked"]["lng"]
                    st.write(lat)
                    st.write(lon)
