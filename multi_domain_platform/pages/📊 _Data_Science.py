import streamlit as st
import pandas as pd
import random
import plotly.express as px
from faker import Faker 
from services.database_manager import DatabaseManager 

# --- CONSTANTS AND INITIALIZATION ---
db = DatabaseManager("intelligence_platform.db")
FAKE = Faker()
# New constants for Data Science/ML Experiments
MODEL_NAMES = ["BERT-Base", "ResNet-50", "XGBoost", "Logistic Regression", "Custom CNN"]
DATASETS = ["ImageNet", "Kaggle-Housing", "Financial-TS", "E-Commerce-Reviews"]
STATUSES = ["Completed", "Running", "Failed", "Pending"]
ML_TABLE_NAME = "ml_experiments" 

# --- Authentication Checks ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must be logged in to view the dashboard.")
    if st.button("Go to login page"):
        st.switch_page("Home.py")
    st.stop()

st.title("📊 Data Science / ML Platform")
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
    """Generates test data and loads it into the 'ml_experiments' table."""
    st.write(f"Generating and loading {num_records} ML experiment records...")
    
    # 1. Check if the table already has data
    try:
        # Use the correct table name here
        data_check = db_manager.fetch_all(f"SELECT id FROM {ML_TABLE_NAME} LIMIT 1")
        if data_check:
            st.success("Database already populated. Skipping initial data load.")
            return
    except Exception:
        # Proceed, assuming the table needs to be created first (this should be handled by DatabaseManager)
        pass 

    # 2. Generate Data
    records = []
    for i in range(1, num_records + 1):
        record = {
            'model_name': random.choice(MODEL_NAMES),
            'dataset': random.choice(DATASETS),
            'status': random.choice(STATUSES),
            'accuracy': round(random.uniform(0.65, 0.99), 4),
            'run_time_seconds': random.randint(300, 3600),
            'timestamp': FAKE.date_time_this_year().strftime("%Y-%m-%d %H:%M:%S")
        }
        records.append(record)

    # 3. Load into DB
    insert_query = f"""
        INSERT INTO {ML_TABLE_NAME} 
        (model_name, dataset, status, accuracy, run_time_seconds, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?)
    """
    
    insert_count = 0
    for record in records:
        params = (
            record['model_name'], 
            record['dataset'], 
            record['status'], 
            record['accuracy'], 
            record['run_time_seconds'],
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
def get_experiment_data_from_db():
    """Fetches all ML experiments directly from the database."""
    query = f"""
        SELECT id, timestamp, model_name, dataset, status, accuracy, run_time_seconds 
        FROM {ML_TABLE_NAME} 
        ORDER BY timestamp DESC
    """
    experiment_data = db.fetch_all(query)
    df = pd.DataFrame(experiment_data)

    if not df.empty:
        st.sidebar.success(f"Loaded {len(df)} ML experiments from database.")
    
    return df

# --- HELPER FUNCTIONS FOR CRUD OPERATIONS ---

def get_experiment_row(df, experiment_id):
    """Retrieves a single experiment row (Series) by ID."""
    if experiment_id is None: return None
    filtered_df = df[df['id'] == experiment_id]
    return filtered_df.iloc[0] if not filtered_df.empty else None

def handle_add_experiment(new_data):
    """Handles the 'Create' operation."""
    query = f"""
        INSERT INTO {ML_TABLE_NAME} 
        (model_name, dataset, status, accuracy, run_time_seconds) 
        VALUES (?, ?, ?, ?, ?)
    """
    params = (
        new_data['model_name'], 
        new_data['dataset'], 
        new_data.get('status', 'Pending'), # Default to Pending
        new_data['accuracy'],
        new_data['run_time_seconds']
    )
    rowcount, new_id = db.execute_query(query, params)
    
    st.cache_data.clear()
    st.session_state['experiment_df'] = get_experiment_data_from_db()
    if rowcount > 0:
        st.success(f"Experiment '{new_data['model_name']}' added successfully. ID: {new_id}")
    else:
        st.error("Failed to add experiment.")

def handle_update_experiment(experiment_id, updated_data):
    """Handles the 'Update' operation."""
    query = f"""
        UPDATE {ML_TABLE_NAME} 
        SET model_name = ?, dataset = ?, status = ?, accuracy = ?, run_time_seconds = ?
        WHERE id = ?
    """
    params = (
        updated_data['model_name'], 
        updated_data['dataset'], 
        updated_data['status'], 
        updated_data['accuracy'], 
        updated_data['run_time_seconds'], 
        experiment_id
    )
    rowcount, _ = db.execute_query(query, params)
    
    st.cache_data.clear()
    st.session_state['experiment_df'] = get_experiment_data_from_db()
    if rowcount > 0:
        st.success(f"Experiment ID {experiment_id} updated successfully.")
    else:
        st.error(f"Experiment ID {experiment_id} not found for update.")

def handle_delete_experiment(experiment_id):
    """Handles the 'Delete' operation."""
    query = f"DELETE FROM {ML_TABLE_NAME} WHERE id = ?"
    rowcount, _ = db.execute_query(query, (experiment_id,))
    
    st.cache_data.clear()
    st.session_state['experiment_df'] = get_experiment_data_from_db()
    if rowcount > 0:
        st.success(f"Experiment ID {experiment_id} deleted successfully.")
    else:
        st.error(f"Experiment ID {experiment_id} not found for deletion.")

# --- INITIALIZATION (Load the DataFrame) ---

if 'experiment_df' not in st.session_state:
    st.session_state['experiment_df'] = get_experiment_data_from_db()

df = st.session_state['experiment_df']

# --- STREAMLIT PAGE FUNCTIONS ---

def display_dashboard(df):
    """Renders the main dashboard metrics and charts."""
    st.title("Machine Learning Dashboard Overview")
    
    if df.empty:
        st.info("No experiments to display.")
        return
        
    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    
    total_experiments = len(df)
    completed_experiments = df[df['status'] == 'Completed'].shape[0] if 'status' in df.columns else 0
    # Calculate average accuracy of completed models
    avg_accuracy = df[df['status'] == 'Completed']['accuracy'].mean() if 'accuracy' in df.columns else 0

    col1.metric("Total Experiments", total_experiments)
    col2.metric("Completed Experiments", completed_experiments)
    col3.metric("Avg Completed Accuracy", f"{avg_accuracy:.2%}" if avg_accuracy > 0 else "N/A")

    st.markdown("---")
    
    # --- Charts Section ---
    st.header("Experiment Analysis")
    chart_col1, chart_col2 = st.columns(2)

    # 1. Bar Chart: Experiments by Dataset
    if 'dataset' in df.columns:
        dataset_counts = df['dataset'].value_counts().reset_index()
        dataset_counts.columns = ['Dataset', 'Count']
        
        fig_bar = px.bar(
            dataset_counts, 
            x='Dataset', 
            y='Count', 
            title='Experiments by Dataset'
        )
        chart_col1.plotly_chart(fig_bar, use_container_width=True)

    # 2. Scatter Plot: Accuracy vs. Runtime (for Completed experiments)
    completed_df = df[df['status'] == 'Completed']
    if 'accuracy' in completed_df.columns and 'run_time_seconds' in completed_df.columns:
        fig_scatter = px.scatter(
            completed_df, 
            x='run_time_seconds', 
            y='accuracy', 
            color='model_name',
            title='Model Accuracy vs. Runtime (Completed)',
            hover_data=['dataset']
        )
        chart_col2.plotly_chart(fig_scatter, use_container_width=True)
    else:
        chart_col2.info("Cannot plot Accuracy vs. Runtime. Missing data.")


    st.markdown("---")

    # --- Data Table Section (Experiment Log) ---
    st.header("All ML Experiment Data")
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True, height=350)

def display_crud_form(df):
    """Renders the Add Experiment (Create), Update, and Delete forms using tabs."""
    st.title("Experiment Management")
    
    can_manage = 'id' in df.columns

    # Button to load initial data if table is empty
    if df.empty:
        st.info("No ML experiments found. Click the button to load test data.")
        if st.button("Load 1000 Initial Experiments", type="primary"):
            generate_and_load_data(db, 1000)
            
    # --- TAB DEFINITION ---
    create_tab, update_tab, delete_tab = st.tabs(["➕ Create New", "✏️ Update Existing", "🗑️ Delete Experiment"])
    
    # --- CREATE TAB ---
    with create_tab:
        st.subheader("Add New Experiment")
        
        with st.form("add_experiment_form", clear_on_submit=True):
            
            new_model = st.selectbox("Model Name", MODEL_NAMES, key="new_model_c")
            new_dataset = st.selectbox("Dataset", DATASETS, key="new_dataset_c")
            
            # Use number inputs for metrics
            new_accuracy = st.number_input("Accuracy (0.0 to 1.0)", min_value=0.0, max_value=1.0, value=0.85, step=0.01, key="new_accuracy_c")
            new_runtime = st.number_input("Run Time (seconds)", min_value=1, value=600, step=10, key="new_runtime_c")
            
            new_status = st.selectbox("Status", STATUSES, index=3, key="new_status_c") # Default to Pending

            submitted = st.form_submit_button("Submit New Experiment", type="primary")
            
            if submitted:
                if new_model and new_dataset:
                    new_data = {
                        'model_name': new_model,
                        'dataset': new_dataset,
                        'status': new_status,
                        'accuracy': new_accuracy,
                        'run_time_seconds': new_runtime
                    }
                    handle_add_experiment(new_data)
                else:
                    st.error("Please enter the experiment details.")

    # --- UPDATE TAB ---
    with update_tab:
        if can_manage and not df.empty:
            st.subheader("Update Experiment Details")
            
            experiment_ids = df['id'].sort_values().tolist()
            
            selected_update_id = st.selectbox("Select Experiment ID to Update", [""] + experiment_ids, key='update_id_select')
            
            if selected_update_id != "":
                selected_update_id = int(selected_update_id)
                current_data = get_experiment_row(df, selected_update_id)
                
                if current_data is not None:
                    with st.form("update_experiment_form"):
                        current_model = current_data.get('model_name', MODEL_NAMES[0])
                        current_dataset = current_data.get('dataset', DATASETS[0])
                        current_status = current_data.get('status', STATUSES[0])
                        current_accuracy = current_data.get('accuracy', 0.0)
                        current_runtime = current_data.get('run_time_seconds', 0)
                        
                        st.caption(f"Editing Experiment ID: **{selected_update_id}** - Model: **{current_model}**")
                        
                        upd_model = st.selectbox(
                            "New Model Name", 
                            MODEL_NAMES, 
                            index=MODEL_NAMES.index(current_model) if current_model in MODEL_NAMES else 0
                        )
                        upd_dataset = st.selectbox(
                            "New Dataset", 
                            DATASETS, 
                            index=DATASETS.index(current_dataset) if current_dataset in DATASETS else 0
                        )
                        upd_status = st.selectbox(
                            "New Status", 
                            STATUSES, 
                            index=STATUSES.index(current_status) if current_status in STATUSES else 0
                        )
                        upd_accuracy = st.number_input(
                            "New Accuracy (0.0 to 1.0)", 
                            min_value=0.0, max_value=1.0, 
                            value=current_accuracy, step=0.01
                        )
                        upd_runtime = st.number_input(
                            "New Run Time (seconds)", 
                            min_value=1, 
                            value=int(current_runtime), step=10
                        )
                        
                        update_submitted = st.form_submit_button("Apply Update", type="primary")
                        
                        if update_submitted:
                            updated_data = {
                                'model_name': upd_model,
                                'dataset': upd_dataset,
                                'status': upd_status,
                                'accuracy': upd_accuracy,
                                'run_time_seconds': upd_runtime
                            }
                            handle_update_experiment(selected_update_id, updated_data)
                else:
                    st.info(f"Experiment ID {selected_update_id} not found in current data.")
            else:
                st.info("Select an Experiment ID to begin updating.")
        else:
            st.info("No experiments available to update.")
        
    # --- DELETE TAB ---
    with delete_tab:
        if can_manage and not df.empty:
            st.subheader("Delete Experiment")
            
            delete_ids = df['id'].sort_values().tolist()
            
            selected_delete_id = st.selectbox("Select Experiment ID to Delete", [""] + delete_ids, key='delete_id_select_2')

            if selected_delete_id != "":
                selected_delete_id = int(selected_delete_id)
                current_data = get_experiment_row(df, selected_delete_id)
                
                st.warning(f"Are you sure you want to delete Experiment ID: **{selected_delete_id}** (Model: {current_data.get('model_name', 'N/A')})? This cannot be undone.")

                if st.button("Confirm Delete", type="primary"):
                    handle_delete_experiment(selected_delete_id)
            else:
                st.info("Select an Experiment ID to delete.")
        else:
            st.info("No experiments available to delete.")

    st.markdown("---")
    
    st.subheader("Current Experiments List (Live View)")
    # Sort the table to show newest experiments first for better visibility of CRUD operations
    if 'timestamp' in df.columns:
        df = df.sort_values(by='timestamp', ascending=False)
    st.dataframe(df, use_container_width=True)


# --- MAIN APPLICATION LOGIC ---

# Use sidebar radio button to switch between views
page = st.sidebar.radio("Navigate Views", ["Dashboard Overview", "Experiment Management (CRUD)"])

# Display the main content based on the sidebar selection
if page == "Dashboard Overview":
    display_dashboard(st.session_state['experiment_df'])
elif page == "Experiment Management (CRUD)":
    display_crud_form(st.session_state['experiment_df'])