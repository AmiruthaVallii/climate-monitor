# pylint: disable=line-too-long

"""Streamlit code to create a dashboard homepage"""

import streamlit as st
from modules.nav import navbar


if __name__ == "__main__":
    navbar()
    st.set_page_config(
        page_title="EcoIntel",
        page_icon=".streamlit/favicon.png",
        layout="wide"
    )

    st.title("🌍 EcoIntel Climate Dashboard")
    st.divider()

    st.subheader("Welcome to the EcoIntel Climate Dashboard!")
    st.markdown(
        """
        This dashboard provides **live**, **historic**, and **forecast** data on:

        - 🌦️ Weather
        - 🫁 Air Quality
        - 💧 Flood Alerts

        Use the navigation bar to _**explore how climate change is impacting your area**_.
        """)

    st.markdown("######")

    st.header("🌦️ Weather Dashboard")
    st.markdown(
        """
        This dashboard compares this year's weather readings with historic data (**1940**-**1960**) and future weather predictions (until **2045**).

        It explores the change in **temperature**, **rainfall**, and **wind**, and how this is expected to continue into the future.
        """)

    st.markdown("#####")

    st.header("💧 Flood Dashboard")
    st.markdown(
        """
        This dashboard displays **all live flood warnings** for every tracked location. This contains the location, date and time, description, and a message.

        It also allows you to explore the historical data by location to understand the change in the number of flood alerts in your local region.
        """)

    st.markdown("#####")

    st.header("🫁 Air Quality Dashboard")
    st.markdown(
        """
        This dashboard shows the most recent air quality metrics, and how they have changed since the same time yesterday.
        
        It then compares the change in all metrics over a user-defined time period, for any location desired.
        """)

    st.markdown("#####")

    st.header("🔐 Login / 👤 Profile")
    st.markdown(
        """
        Use the _Login_ page to access your own _Profile_ page.

        The _Profile_ page allows you to browse the tracked locations and choose to sign up for:

        - Alerts
          - Be notified via email whenever there are any flood alerts, if air quality index has reached 4/5 or greater, or if any weather values reached a certain threshold.
        - Daily Summary
          - Receive an email at the end of each day which summarises all of the data from that day.
        """)
