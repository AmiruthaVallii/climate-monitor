"""Module for navigation related functions."""
import streamlit as st


def navbar():
    """Navigation sidebar for the dashboard."""
    with st.sidebar:
        st.image("modules/logo-no-background.png")
        st.page_link('homepage.py', label='Homepage', icon='👋')
        st.page_link('pages/weather.py', label='Weather', icon='🌦️')
        st.page_link('pages/floods.py', label='Floods', icon='💧')
        st.page_link('pages/air_quality.py', label='Air Quality', icon='🫁')
        if st.session_state.get("logged_in"):
            st.page_link('pages/profile.py',
                         label='My Profile', icon='👤')
        else:
            st.page_link('pages/login.py', label='Login',
                         icon="🔐")
