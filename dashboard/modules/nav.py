"""Module for navigation related functions."""
import streamlit as st


def navbar():
    """Navigation sidebar for the dashboard."""
    with st.sidebar:
        st.image("modules/logo-no-background.png")
        st.page_link('login.py', label='Login',
                     icon="🔐")
        st.page_link('pages/profile.py',
                     label='My Profile', icon='👤')
        st.page_link('pages/weather.py', label='Weather', icon='🌦️')
        st.page_link('pages/floods.py', label='Floods', icon='💧')
        st.page_link('pages/air_quality.py', label='Air Quality', icon='🫁')
