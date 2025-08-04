import streamlit as st
import bcrypt
import psycopg2
import os
from dotenv import load_dotenv

st.set_page_config(
    page_title="Eco Intel",
    page_icon=".streamlit/favicon.png",
)

load_dotenv()

# Database connection


def get_conn():
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )

# Register new user


def register_user(first_name, last_name, email, phone, username, password):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users 
                    (first_name, last_name, email, phone_number, username, password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (first_name, last_name, email, phone, username, hashed_pw))
        return True
    except psycopg2.errors.UniqueViolation:
        return False
    except Exception as e:
        st.error(f"Database error: {e}")
        return False


# Login check


def login_user(username, password):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT password FROM users WHERE username = %s", (username,))
                row = cur.fetchone()
                if row and bcrypt.checkpw(password.encode(), row[0].encode()):
                    return True
    except Exception as e:
        st.error(f"Login error: {e}")
    return False


# Streamlit UI
st.title("🔐 Login & Registration")

auth_mode = st.radio("Choose action", ["Login", "Register"])

if auth_mode == "Register":
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type="password")

    if st.button("Register"):
        if all([first_name, last_name, email, phone, new_user, new_pass]):
            success = register_user(
                first_name, last_name, email, phone, new_user, new_pass)
            if success:
                st.success("User registered successfully. You can now log in.")
            else:
                st.error("Username already exists or an error occurred.")
        else:
            st.warning("Please fill in all fields.")

elif auth_mode == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(username, password):
            st.success(f"Welcome {username}!")
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
        else:
            st.error("Invalid username or password.")
