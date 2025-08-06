"""Login/ registeration page of the climate monitor dashboard"""
import os
import streamlit as st
import bcrypt
import psycopg2
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError, EmailSyntaxError, EmailUndeliverableError
import phonenumbers
from modules.nav import navbar


def get_conn():
    """Returns connection to RDS."""
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"]
    )


def is_valid_email(email: str) -> bool:
    """Checks if user entered email is valid."""
    try:
        validate_email(email)
        return True
    except (EmailNotValidError, EmailSyntaxError, EmailUndeliverableError) as e:
        st.error(f"Email error: {str(e)}")
        return False


def is_valid_phone(phone: str) -> bool:
    """Checks if user entered phone number is valid."""
    try:
        parsed = phonenumbers.parse(phone, "GB")
        if not phonenumbers.is_valid_number(parsed):
            st.error("Invalid phone number.")
            return False
    except phonenumbers.NumberParseException as e:
        st.error(f"Phone number error: {str(e)}")
        return False
    return True


def register_user(first_name: str, last_name: str, email: str, phone: str, username: str, password: str) -> bool:  # pylint: disable=too-many-arguments, too-many-positional-arguments
    """Inserts user registeration details into users table in the database.
        - Hashes user entered password first for security."""
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


def login_user(username: str, password: str) -> bool:
    """Fetches hashed password from database and returns True
        if it matches the hashed user entered password."""
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


if __name__ == "__main__":

    load_dotenv()
    navbar()
    st.set_page_config(
        page_title="EcoIntel",
        page_icon=".streamlit/favicon.png",
    )
    st.title("🔐 Login & Registration")
    st.divider()

    auth_mode = st.radio("Choose action", ["Login", "Register"])

    if auth_mode == "Register":
        user_firstname = st.text_input("First Name")
        user_lastname = st.text_input("Last Name")
        user_email = st.text_input("Email")
        user_phone = st.text_input("Phone Number")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            if not all([user_firstname, user_lastname, user_email, user_phone, new_user, new_pass]):
                st.warning("Please fill in all fields.")
            elif not is_valid_email(user_email):
                pass
            elif not is_valid_phone(user_phone):
                pass
            else:
                SUCCESS = register_user(user_firstname, user_lastname,
                                        user_email, user_phone, new_user, new_pass)
                if SUCCESS:
                    st.success(
                        "User registered successfully. You can now log in.")
                else:
                    st.error(
                        "Username or email already exists, or an error occurred.")

    elif auth_mode == "Login":
        inputted_username = st.text_input("Username")
        inputted_password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(inputted_username, inputted_password):
                st.success(f"Welcome {inputted_username}!")
                st.session_state["logged_in"] = True
                st.session_state["username"] = inputted_username
                st.switch_page("pages/profile.py")
            else:
                st.error("Invalid username or password.")
