import streamlit as st
import pandas as pd
import random
import plotly.express as px
from faker import Faker 
from services.database_manager import DatabaseManager 

# --- CONSTANTS AND INITIALIZATION ---
db = DatabaseManager("intelligence_platform.db")
FAKE = Faker()
INCIDENT_TYPES = ["Malware Infection", "Phishing Attempt", "Unauthorized Access", "DDoS Attack", "Data Exfiltration", "System Misconfiguration"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
STATUSES = ["Open", "In Progress", "Closed", "Pending Review"]
INCIDENT_TABLE_NAME = "security_incidents"

# --- Authentication Checks ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must be logged in to view the dashboard.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("🛡️ Security Incidents Dashboard")
st.success(f"Hello, **{st.session_state.username}**! You are logged in.")

# Logout button
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.info("You have been logged out.")
    st.switch_page("Home.py")


# --- Data Generation & Loading Function ---

def generate_and_load_data(db_manager, num_records=1000):
    """Generates test data and loads it into the 'security_incidents' table."""
    st.write(f"Generating and loading {num_records} incident records...")
    
    # 1. Check if the table already has data
    try:
        data_check = db_manager.fetch_all(f"SELECT id FROM {INCIDENT_TABLE_NAME} LIMIT 1")
        if data_check:
            st.success("Database already populated. Skipping initial data load.")
            return
    except Exception:
        pass 

    # 2. Generate Data
    records = []
    for i in range(1, num_records + 1):
        record = {
            'incident_type': random.choice(INCIDENT_TYPES),
            'severity': random.choice(SEVERITIES),
            'status': random.choice(STATUSES),
            'description': FAKE.sentence(nb_words=10),
            'timestamp': FAKE.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        }
        records.append(record)

    # 3. Load into DB
    insert_query = f"""
        INSERT INTO {INCIDENT_TABLE_NAME} 
        (incident_type, severity, status, description, timestamp) 
        VALUES (?, ?, ?, ?, ?)
    """
    
    insert_count = 0
    for record in records:
        params = (
            record['incident_type'], 
            record['severity'], 
            record['status'], 
            record['description'], 
            record['timestamp']
        )
        rowcount, _ = db_manager.execute_query(insert_query, params)
        if rowcount > 0:
            insert_count += 1
            
    st.success(f"Successfully loaded {insert_count} records into the database!")
    st.cache_data.clear()
    st.rerun() 


# --- Data Reading and Caching ---

@st.cache_data(ttl=60)
def get_incident_data_from_db():
    """Fetches all incidents directly from the database."""
    query = f"SELECT id, timestamp, incident_type, severity, status, description FROM {INCIDENT_TABLE_NAME} ORDER BY timestamp DESC"
    incident_data = db.fetch_all(query)
    df = pd.DataFrame(incident_data)

    if not df.empty:
        st.sidebar.success(f"Loaded {len(df)} incidents from database.")
    
    return df

# --- HELPER FUNCTIONS FOR CRUD OPERATIONS ---

def get_incident_row(df, incident_id):
    """Retrieves a single incident row (Series) by ID."""
    if incident_id is None: return None
    filtered_df = df[df['id'] == incident_id]
    return filtered_df.iloc[0] if not filtered_df.empty else None

def handle_add_incident(new_data):
    """Handles the 'Create' operation."""
    query = f"""
        INSERT INTO {INCIDENT_TABLE_NAME} 
        (incident_type, severity, status, description) 
        VALUES (?, ?, 'Open', ?)
    """
    rowcount, new_id = db.execute_query(query, (new_data['incident_type'], new_data['severity'], new_data['description']))
    
    st.cache_data.clear()
    st.session_state['incident_df'] = get_incident_data_from_db()
    if rowcount > 0:
        st.success(f"Incident '{new_data['incident_type']}' added successfully. ID: {new_id}")
    else:
        st.error("Failed to add incident.")

def handle_update_incident(incident_id, updated_data):
    """Handles the 'Update' operation."""
    query = f"""
        UPDATE {INCIDENT_TABLE_NAME} 
        SET incident_type = ?, severity = ?, status = ?, description = ? 
        WHERE id = ?
    """
    rowcount, _ = db.execute_query(
        query, 
        (updated_data['incident_type'], updated_data['severity'], updated_data['status'], updated_data['description'], incident_id)
    )
    
    st.cache_data.clear()
    st.session_state['incident_df'] = get_incident_data_from_db()
    if rowcount > 0:
        st.success(f"Incident ID {incident_id} updated successfully.")
    else:
        st.error(f"Incident ID {incident_id} not found for update.")

def handle_delete_incident(incident_id):
    """Handles the 'Delete' operation."""
    query = f"DELETE FROM {INCIDENT_TABLE_NAME} WHERE id = ?"
    rowcount, _ = db.execute_query(query, (incident_id,))
    
    st.cache_data.clear()
    st.session_state['incident_df'] = get_incident_data_from_db()
    if rowcount > 0:
        st.success(f"Incident ID {incident_id} deleted successfully.")
    else:
        st.error(f"Incident ID {incident_id} not found for deletion.")

# --- INITIALIZATION (Load the DataFrame) ---

# Load the DataFrame from the DB only once, or refresh it on demand
if 'incident_df' not in st.session_state:
    st.session_state['incident_df'] = get_incident_data_from_db()

df = st.session_state['incident_df']

# Check if data needs to be initialized (Button is inside display_crud_form now, but we need the check here)
if df.empty:
    st.info("No incidents found in the database. Use the sidebar menu to go to 'Incident Management (CRUD)' to load test data.")
    
# --- STREAMLIT PAGE FUNCTIONS ---

def display_dashboard(df):
    """Renders the main dashboard metrics and charts and Incident Log."""
    st.title("Incidents Dashboard Overview")

    if df.empty:
        st.info("No incidents to display.")
        return
        
    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    
    total_incidents = len(df)
    open_incidents = df[df['status'] == 'Open'].shape[0] if 'status' in df.columns else 0
    critical_incidents = df[df['severity'] == 'Critical'].shape[0] if 'severity' in df.columns else 0

    col1.metric("Total Incidents", total_incidents)
    col2.metric("Open Incidents", open_incidents)
    col3.metric("Critical Incidents", critical_incidents)

    st.markdown("---")
    
    # --- Charts Section ---
    st.header("Incident Analysis")
    chart_col1, chart_col2 = st.columns(2)

    # 1. Bar Chart: Incidents by Severity
    if 'severity' in df.columns:
        severity_counts = df['severity'].value_counts().reindex(SEVERITIES, fill_value=0).reset_index()
        severity_counts.columns = ['Severity', 'Count']
        
        color_map = {
            "Critical": "red", "Migh": "orange", 
            "Medium": "gold", "Low": "green"
        }
        
        fig_bar = px.bar(
            severity_counts, 
            x='Severity', 
            y='Count', 
            title='Count of Incidents by Severity',
            category_orders={"Severity": SEVERITIES},
            color='Severity',
            color_discrete_map=color_map
        )
        chart_col1.plotly_chart(fig_bar, use_container_width=True)

    # 2. Pie Chart: Distribution of Incident Types
    if 'incident_type' in df.columns:
        type_counts = df['incident_type'].value_counts().reset_index()
        type_counts.columns = ['Incident_Type', 'Count']
        
        fig_pie = px.pie(
            type_counts, 
            names='Incident_Type', 
            values='Count', 
            title='Distribution of Incident Types',
        )
        chart_col2.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- Data Table Section (Incident Log) ---
    st.header("All Incidents Data")
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True, height=350)

def display_crud_form(df):
    """Renders the Add Incident (Create), Update, and Delete forms using tabs."""
    st.title("Incident Management")
    
    can_manage = 'id' in df.columns

    # Button to load initial data if table is empty
    if df.empty:
        st.info("No incidents found. Click the button to load test data.")
        if st.button("Load 1000 Initial Incidents", type="primary"):
            generate_and_load_data(db, 1000)
            
    # --- TAB DEFINITION (Matches desired clean structure) ---
    create_tab, update_tab, delete_tab = st.tabs(["➕ Create New", "✏️ Update Existing", "🗑️ Delete Incident"])
    
    # --- CREATE TAB ---
    with create_tab:
        st.subheader("Add New Incident")
        
        with st.form("add_incident_form", clear_on_submit=True):
            
            new_type = st.selectbox("Incident Type", INCIDENT_TYPES, key="new_type_c")
            new_severity = st.selectbox("Severity Level", SEVERITIES, key="new_severity_c")
            
            new_description = st.text_area("Description", key="new_description_c")
            
            submitted = st.form_submit_button("Submit New Incident", type="primary")
            
            if submitted:
                if new_type and new_description:
                    new_data = {
                        'incident_type': new_type,
                        'severity': new_severity,
                        'description': new_description
                    }
                    handle_add_incident(new_data)
                else:
                    st.error("Please enter the incident details.")

    # --- UPDATE TAB ---
    with update_tab:
        if can_manage and not df.empty:
            st.subheader("Update Incident Details")
            
            # Use the IDs from the database (now in the DataFrame)
            incident_ids = df['id'].sort_values().tolist()
            
            selected_update_id = st.selectbox("Select Incident ID to Update", [""] + incident_ids, key='update_id_select')
            
            if selected_update_id != "":
                selected_update_id = int(selected_update_id)
                current_data = get_incident_row(df, selected_update_id)
                
                if current_data is not None:
                    with st.form("update_incident_form"):
                        current_type = current_data.get('incident_type', INCIDENT_TYPES[0])
                        current_severity = current_data.get('severity', SEVERITIES[0])
                        current_status = current_data.get('status', STATUSES[0])
                        current_description = current_data.get('description', '')
                        
                        st.caption(f"Editing Incident ID: **{selected_update_id}** - Type: **{current_type}**")
                        
                        upd_type = st.selectbox(
                            "New Incident Type", 
                            INCIDENT_TYPES, 
                            index=INCIDENT_TYPES.index(current_type) if current_type in INCIDENT_TYPES else 0
                        )
                        upd_severity = st.selectbox(
                            "New Severity Level", 
                            SEVERITIES, 
                            index=SEVERITIES.index(current_severity) if current_severity in SEVERITIES else 0
                        )
                        upd_status = st.selectbox(
                            "New Status", 
                            STATUSES, 
                            index=STATUSES.index(current_status) if current_status in STATUSES else 0
                        )
                        upd_description = st.text_area("New Description", value=current_description)
                        
                        update_submitted = st.form_submit_button("Apply Update", type="primary")
                        
                        if update_submitted:
                            updated_data = {
                                'incident_type': upd_type,
                                'severity': upd_severity,
                                'status': upd_status,
                                'description': upd_description
                            }
                            handle_update_incident(selected_update_id, updated_data)
                else:
                    st.info(f"Incident ID {selected_update_id} not found in current data.")
            else:
                st.info("Select an Incident ID to begin updating.")
        else:
            st.info("No incidents available to update.")
        
    # --- DELETE TAB ---
    with delete_tab:
        if can_manage and not df.empty:
            st.subheader("Delete Incident")
            
            delete_ids = df['id'].sort_values().tolist()
            
            selected_delete_id = st.selectbox("Select Incident ID to Delete", [""] + delete_ids, key='delete_id_select_2')

            if selected_delete_id != "":
                selected_delete_id = int(selected_delete_id)
                current_data = get_incident_row(df, selected_delete_id)
                
                st.warning(f"Are you sure you want to delete Incident ID: **{selected_delete_id}** (Type: {current_data.get('incident_type', 'N/A')})? This cannot be undone.")

                if st.button("Confirm Delete", type="primary"):
                    handle_delete_incident(selected_delete_id)
            else:
                st.info("Select an Incident ID to delete.")
        else:
            st.info("No incidents available to delete.")

    st.markdown("---")
    
    st.subheader("Current Incidents List (Live View)")
    # Sort the table to show newest incidents first for better visibility of CRUD operations
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True)


# --- MAIN APPLICATION LOGIC ---

st.set_page_config(layout="wide")

# Use sidebar radio button to switch between views
page = st.sidebar.radio("Navigate Views", ["Dashboard Overview", "Incident Management (CRUD)"])

# Display the main content based on the sidebar selection
if page == "Dashboard Overview":
    display_dashboard(st.session_state['incident_df'])
elif page == "Incident Management (CRUD)":
    display_crud_form(st.session_state['incident_df'])