import streamlit as st
# NOTE: Assuming the import path below is correct for your file structure
from auth import login_user,register_user, validate_username, validate_password # Added imports
import os
import sys

st.set_page_config(page_title="Login / Register", page_icon="🔑", layout="centered")

# ---------- Initialise session state ----------
if "users" not in st.session_state:
    # We will no longer rely on this simple dictionary for user storage. 
    # The register_user and login_user functions will handle persistence 
    # with the 'users.txt' file and use proper hashing.
    st.session_state.users = {} 

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

st.title("🔐 Welcome")

# If already logged in, go straight to dashboard (optional)
if st.session_state.logged_in:
    st.success(f"Already logged in as **{st.session_state.username}**.")
    if st.button("Go to dashboard"):
        # Use the official navigation API to switch pages
        st.switch_page("pages/1_Dashboard.py")  # path is relative to Home.py 
    st.stop()  # Don’t show login/register again


# ---------- Tabs: Login / Register ----------
tab_login, tab_register = st.tabs(["Login", "Register"])

# ----- LOGIN TAB -----
with tab_login:
    st.subheader("Login")

    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log in", type="primary"):
        # Using the secure login_user function from auth.py
        if login_user(login_username, login_password):
            st.session_state.logged_in = True
            st.session_state.username = login_username
            st.success(f"Welcome back, {login_username}! ")

            # Redirect to dashboard page
            st.switch_page("pages/1_Dashboard.py")
        else:
            # The login_user function already prints the error (not found or bad password), 
            # but we can show a general error in the UI.
            st.error("Login failed. Check your username and password.")


# ----- REGISTER TAB -----
with tab_register:
    st.subheader("Register")

    new_username = st.text_input("Choose a username", key="register_username")
    new_password = st.text_input("Choose a password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm password", type="password", key="register_confirm")

    if st.button("Create account"):
        # 1. Check if passwords match
        if new_password != confirm_password:
            st.error("Error: Passwords do not match.")
        
        # 2. Run the validation checks from auth.py
        else:
            # Validate Username
            ok_u, msg_u = validate_username(new_username)
            if not ok_u:
                st.error(f"Error: {msg_u}")
                
            # Validate Password
            ok_p, msg_p = validate_password(new_password)
            if not ok_p:
                st.error(f"Error: {msg_p}")
            
            # 3. If both are valid, attempt registration
            if ok_u and ok_p:
                # Use the register_user function, which handles hashing and saving to users.txt
                # Note: register_user also internally checks if the user exists.
                if register_user(new_username, new_password):
                    st.success("Account created! You can now log in from the Login tab.")
                    st.info("Tip: go to the Login tab and sign in with your new account.")
                else:
                    # register_user prints the error (e.g., user exists) to the console, 
                    # but we should show it on the UI if we know it failed.
                    st.error("Registration failed. This username may already be taken.")