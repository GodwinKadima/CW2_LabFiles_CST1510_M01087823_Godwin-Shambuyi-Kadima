import streamlit as st
# External services required for authentication
from services.database_manager import DatabaseManager 
from services.auth_manager import AuthManager 

# Initialize services
db = DatabaseManager("intelligence_platform.db")
auth = AuthManager(db)

st.set_page_config(page_title="Login / Register", page_icon="🔑", layout="centered")

# --- Session State Initialization ---
if "users" not in st.session_state:
    st.session_state.users = {} 
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("🔐 Multi domain Platform")

# --- Logged-In State ---
if st.session_state.logged_in:
    st.success(f"Already logged in as **{st.session_state.username}**.")
    if st.button("Go to dashboard"):
        # SWITCHED TO CYBERSECURITY PAGE PATH
        st.switch_page("pages/_🛡️ _Cybersecurity.py") 
    st.stop()


# --- Tabs: Login / Register ---
tab_login, tab_register = st.tabs(["Login", "Register"])

# --- LOGIN TAB ---
with tab_login:
    st.subheader("Login")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log in", type="primary"):
        if auth.login(login_username, login_password):
            st.session_state.logged_in = True
            st.session_state.username = login_username
            st.success(f"Welcome back, {login_username}! ")
            # SWITCHED TO CYBERSECURITY PAGE PATH
            st.switch_page("pages/_🛡️ _Cybersecurity.py") 
        else:
            st.error("Login failed. Check your username and password.")


# --- REGISTER TAB ---
with tab_register:
    st.subheader("Register")
    new_username = st.text_input("Choose a username", key="register_username")
    new_password = st.text_input("Choose a password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm password", type="password", key="register_confirm")

    if st.button("Create account"):
        validation_passed = True
        
        # 1. Check if passwords match
        if new_password != confirm_password:
            st.error("Error: Passwords do not match.")
            validation_passed = False
            
        # 2. Validate Username and Password using AuthManager methods
        ok_u, msg_u = auth.validate_username(new_username)
        if not ok_u:
            st.error(f"Username Error: {msg_u}")
            validation_passed = False
            
        ok_p, msg_p = auth.validate_password(new_password)
        if not ok_p:
            st.error(f"Password Error: {msg_p}")
            validation_passed = False
            
        # 3. Attempt registration
        if validation_passed:
            if auth.register_user(new_username, new_password):
                st.success("Account created! You can now log in.")
                st.info("Tip: go to the Login tab and sign in.")
            else:
                st.error("Registration failed. This username may already be taken.")