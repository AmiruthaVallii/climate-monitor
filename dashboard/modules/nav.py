import streamlit as st


def navbar():
    with st.sidebar:
        st.page_link('login.py', label='Login',
                     icon="🔐")
        st.page_link('pages/profile.py',
                     label='My Profile', icon='👤')
        st.page_link('pages/weather.py', label='Weather', icon='🌦️')
        st.page_link('pages/floods.py', label='Floods', icon='💧')
        st.page_link('pages/air_quality.py', label='Air Quality', icon='🫁')
