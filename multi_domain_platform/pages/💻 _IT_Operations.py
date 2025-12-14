import streamlit as st 
import pandas as pd
import plotly.express as px
from datetime import datetime 
import random
from faker import Faker

# Import the DatabaseManager
from services.database_manager import DatabaseManager 
# Removed: from services.ticket_manager import TicketManager

# --- CONSTANTS AND INITIALIZATION ---
db = DatabaseManager("intelligence_platform.db")
FAKE = Faker()
TICKET_STATUSES = ['Open', 'In Progress', 'Closed']
TICKET_SEVERITIES = ['Low', 'Medium', 'High', 'Critical']
TICKET_TABLE_NAME = "it_tickets"

# --- Authentication Checks ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must be logged in to view the dashboard.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("📊 IT Operations Dashboard")
st.success(f"Hello, **{st.session_state.username}**! You are logged in.")

# Logout button
st.divider()
if st.button("Log out"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.info("You have been logged out.")
    st.switch_page("Home.py")

# --- DATA GENERATION & LOADING (Replaced TicketManager.initialize_data) ---

def initialize_data(db_manager, num_records=1000):
    """Generates and loads test data directly into the database."""
    st.write(f"Generating and loading {num_records} IT ticket records...")
    
    records = []
    for i in range(1, num_records + 1):
        records.append({
            'title': FAKE.catch_phrase(),
            'severity': random.choice(TICKET_SEVERITIES),
            'status': random.choice(TICKET_STATUSES),
            'timestamp': FAKE.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        })

    insert_query = f"""
        INSERT INTO {TICKET_TABLE_NAME} 
        (title, severity, status, timestamp) 
        VALUES (?, ?, ?, ?)
    """
    
    insert_count = 0
    for record in records:
        params = (
            record['title'], 
            record['severity'], 
            record['status'], 
            record['timestamp']
        )
        rowcount, _ = db_manager.execute_query(insert_query, params)
        if rowcount > 0:
            insert_count += 1
            
    st.success(f"Successfully loaded {insert_count} records into the database!")
    return insert_count

# --- DATA READING AND CACHING (Updated to use db.fetch_all) ---

@st.cache_data(ttl=60)
def get_tickets_data_from_db():
    """Fetches all tickets directly from the database."""
    query = f"SELECT id, title, severity, status, timestamp FROM {TICKET_TABLE_NAME} ORDER BY timestamp DESC"
    ticket_data = db.fetch_all(query)
    df = pd.DataFrame(ticket_data)

    if not df.empty:
        st.sidebar.success(f"Loaded {len(df)} tickets from database.")
    
    return df

# --- HELPER FUNCTIONS FOR CRUD OPERATIONS (Updated to use db.execute_query) ---

def get_ticket_row(df, ticket_id):
    """Retrieves a single ticket row (Series) by ID."""
    if ticket_id is None: return None
    filtered_df = df[df['id'] == ticket_id]
    return filtered_df.iloc[0] if not filtered_df.empty else None

def handle_add_ticket(new_data):
    """Handles the 'Create' operation."""
    query = f"""
        INSERT INTO {TICKET_TABLE_NAME} 
        (title, severity, status) 
        VALUES (?, ?, 'Open')
    """
    rowcount, new_id = db.execute_query(query, (new_data['title'], new_data['severity']))
    
    st.cache_data.clear()
    st.session_state['tickets_df'] = get_tickets_data_from_db()
    if rowcount > 0:
        st.success(f"Ticket '{new_data['title']}' added successfully. ID: {new_id}")
    else:
        st.error("Failed to add ticket.")

def handle_update_ticket(ticket_id, updated_data):
    """Handles the 'Update' operation."""
    query = f"""
        UPDATE {TICKET_TABLE_NAME} 
        SET title = ?, severity = ?, status = ? 
        WHERE id = ?
    """
    rowcount, _ = db.execute_query(
        query, 
        (updated_data['title'], updated_data['severity'], updated_data['status'], ticket_id)
    )
    
    st.cache_data.clear()
    st.session_state['tickets_df'] = get_tickets_data_from_db()
    if rowcount > 0:
        st.success(f"Ticket ID {ticket_id} updated successfully.")
    else:
        st.error(f"Ticket ID {ticket_id} not found for update.")

def handle_delete_ticket(ticket_id):
    """Handles the 'Delete' operation."""
    query = f"DELETE FROM {TICKET_TABLE_NAME} WHERE id = ?"
    rowcount, _ = db.execute_query(query, (ticket_id,))
    
    st.cache_data.clear()
    st.session_state['tickets_df'] = get_tickets_data_from_db()
    if rowcount > 0:
        st.success(f"Ticket ID {ticket_id} deleted successfully.")
    else:
        st.error(f"Ticket ID {ticket_id} not found for deletion.")


# --- INITIALIZATION (Load the DataFrame) ---

if 'tickets_df' not in st.session_state:
    st.session_state['tickets_df'] = get_tickets_data_from_db()

df = st.session_state['tickets_df']

# Check if data needs to be initialized
if df.empty:
    st.info("No tickets found in the database. Click the button in the sidebar to load test data.")
    if st.sidebar.button("Load 1000 Initial Tickets"):
        initialize_data(db, 1000)
        st.cache_data.clear()
        st.session_state['tickets_df'] = get_tickets_data_from_db()
        st.rerun()

# --- STREAMLIT PAGE FUNCTIONS ---

def display_dashboard(df):
    """Renders the main dashboard metrics and charts."""
    st.title("Tickets Dashboard Overview")

    if df.empty:
        return
        
    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    
    total_tickets = len(df)
    open_tickets = df[df['status'] == 'Open'].shape[0] if 'status' in df.columns else 0
    critical_tickets = df[df['severity'] == 'Critical'].shape[0] if 'severity' in df.columns else 0

    col1.metric("Total Tickets", total_tickets)
    col2.metric("Open Tickets", open_tickets)
    col3.metric("Critical Tickets", critical_tickets)

    st.markdown("---")

    # --- Charts Section ---
    st.header("Ticket Analysis")
    chart_col1, chart_col2 = st.columns(2)

    if 'severity' in df.columns:
        severity_counts = df['severity'].value_counts().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        fig_severity = px.pie(
            severity_counts, 
            values='Count', 
            names='Severity', 
            title='Tickets by Severity',
            color_discrete_sequence=px.colors.sequential.Plasma_r 
        )
        chart_col1.plotly_chart(fig_severity, use_container_width=True)

    if 'status' in df.columns:
        status_counts = df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_status = px.bar(
            status_counts, 
            x='Status', 
            y='Count', 
            title='Tickets by Status',
            color='Status',
            color_discrete_map={'Open': '#EF4444', 'In Progress': '#F59E0B', 'Closed': '#10B981'},
        )
        chart_col2.plotly_chart(fig_status, use_container_width=True)

    st.markdown("---")

    # --- Data Table Section ---
    st.header("All Tickets Data")
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True, height=350)


def display_crud_form(df):
    """Renders the Add Ticket (Create), Update, and Delete forms using tabs."""
    st.title("Ticket Management")
    
    can_manage = 'id' in df.columns

    # --- TAB DEFINITION (Matches desired clean structure) ---
    create_tab, update_tab, delete_tab = st.tabs(["➕ Create New", "✏️ Update Existing", "🗑️ Delete Ticket"])
    
    # --- CREATE TAB ---
    with create_tab:
        st.subheader("Add New Ticket")
        
        with st.form("add_ticket_form", clear_on_submit=True):
            
            new_title = st.text_input("Ticket Title", max_chars=100)
            new_severity = st.selectbox("Severity Level", TICKET_SEVERITIES)
            
            submitted = st.form_submit_button("Submit New Ticket", type="primary")
            
            if submitted:
                if new_title:
                    new_data = {
                        'title': new_title,
                        'severity': new_severity
                    }
                    handle_add_ticket(new_data)
                else:
                    st.error("Please enter a title for the ticket.")

    # --- UPDATE TAB ---
    with update_tab:
        if can_manage and not df.empty:
            st.subheader("Update Ticket Details")
            
            # Use the IDs from the database (now in the DataFrame)
            ticket_ids = df['id'].sort_values().tolist()
            
            selected_update_id = st.selectbox("Select Ticket ID to Update", [""] + ticket_ids, key='update_id_select')
            
            if selected_update_id != "":
                selected_update_id = int(selected_update_id)
                current_data = get_ticket_row(df, selected_update_id)
                
                if current_data is not None:
                    with st.form("update_ticket_form"):
                        current_title = current_data.get('title', 'Title Missing')
                        current_severity = current_data.get('severity', 'Medium')
                        current_status = current_data.get('status', 'Open')
                        
                        st.caption(f"Editing Ticket ID: **{selected_update_id}** - Current Title: **{current_title}**")
                        
                        upd_title = st.text_input("New Title", value=current_title, max_chars=100)
                        
                        upd_severity = st.selectbox(
                            "New Severity Level", 
                            TICKET_SEVERITIES, 
                            index=TICKET_SEVERITIES.index(current_severity) if current_severity in TICKET_SEVERITIES else 0
                        )
                        upd_status = st.selectbox(
                            "New Status", 
                            TICKET_STATUSES, 
                            index=TICKET_STATUSES.index(current_status) if current_status in TICKET_STATUSES else 0
                        )
                        
                        update_submitted = st.form_submit_button("Apply Update", type="primary")
                        
                        if update_submitted:
                            updated_data = {
                                'title': upd_title,
                                'severity': upd_severity,
                                'status': upd_status
                            }
                            handle_update_ticket(selected_update_id, updated_data)
                else:
                    st.info(f"Ticket ID {selected_update_id} not found in current data.")
            else:
                st.info("Select a Ticket ID to begin updating.")
        else:
            st.info("No tickets available to update.")
        
    # --- DELETE TAB ---
    with delete_tab:
        if can_manage and not df.empty:
            st.subheader("Delete Ticket")
            
            delete_ids = df['id'].sort_values().tolist()
            
            selected_delete_id = st.selectbox("Select Ticket ID to Delete", [""] + delete_ids, key='delete_id_select_2')

            if selected_delete_id != "":
                selected_delete_id = int(selected_delete_id)
                current_data = get_ticket_row(df, selected_delete_id)
                
                st.warning(f"Are you sure you want to delete Ticket ID: **{selected_delete_id}** (Title: {current_data.get('title', 'N/A')})? This cannot be undone.")

                if st.button("Confirm Delete", type="primary"):
                    handle_delete_ticket(selected_delete_id)
            else:
                st.info("Select a Ticket ID to delete.")
        else:
            st.info("No tickets available to delete.")

    st.markdown("---")
    
    st.subheader("Current Tickets List (Live View)")
    
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True)


# --- MAIN APPLICATION LOGIC ---

st.set_page_config(layout="wide")

# Use sidebar radio button to switch between views
page = st.sidebar.radio("Navigate Views", ["Dashboard Overview", "Ticket Management (CRUD)"])

# Display the main content based on the sidebar selection
if page == "Dashboard Overview":
    display_dashboard(df)
elif page == "Ticket Management (CRUD)":
    display_crud_form(df)