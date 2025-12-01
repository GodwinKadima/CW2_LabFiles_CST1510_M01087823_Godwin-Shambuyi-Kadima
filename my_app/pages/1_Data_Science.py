import os 
import sys
import streamlit as st 
import pandas as pd
import plotly.express as px
from datetime import datetime 

# --- CRITICAL: DEFINE YOUR CSV FILE PATH ---

def get_data_path(filename):
   
    # Get the directory of the current script (e.g., /.../my_app/pages/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels to reach the project root directory (../../)
    project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    # Combine root, DATA folder (using correct capitalization), and filename 
    return os.path.join(project_root, "DATA", filename)

# Use the function to get the correct path
CSV_FILE_PATH = get_data_path("datasets_metadata_1000.csv")
# ---------------------------------------------


# --- Custom Function to Read Data from CSV ---

@st.cache_data
def get_datasets_from_csv():
    """Reads data from the CSV file. If the file is not found, it creates dummy data."""
    try:
        # 1. Read the actual CSV file using the calculated path
        datasets_df = pd.read_csv(CSV_FILE_PATH, index_col=False)
        
        # 2. Basic cleanup and type conversion 
        if 'timestamp' in datasets_df.columns:
            # Convert timestamp column to datetime objects
            datasets_df['timestamp'] = pd.to_datetime(datasets_df['timestamp'], errors='coerce')
        
        st.sidebar.success(f"Loaded {len(datasets_df)} incidents from CSV.")
        return datasets_df
        
    except FileNotFoundError:
        # NOTE: The error message now displays the path that was attempted
        st.sidebar.error(f"Error: CSV file not found at '{CSV_FILE_PATH}'. Dashboard running on MOCK data.")
        
        # 3. If file not found, generate mock data for demonstration
        data = {
            'id': [101, 102, 103, 104, 105, 106],
            'title': ["Phishing Campaign", "Server Breach", "DDoS Attack", "Misconfiguration", "Insider Threat", "Patching Failure"],
            'severity': ["High", "Critical", "Medium", "Low", "Critical", "Medium"],
            'status': ["Open", "In Progress", "Open", "Closed", "Open", "In Progress"],
            'timestamp': [
                datetime(2025, 11, 20), datetime(2025, 11, 25), datetime(2025, 11, 28),
                datetime(2025, 11, 15), datetime(2025, 11, 29), datetime(2025, 11, 22)
            ]
        }
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error reading CSV file. Check columns names (e.g., severity, status): {e}")
        return pd.DataFrame()


# --- Streamlit App Initialization ---

st.set_page_config(layout="wide")
st.title(" Datasets Dashboard (CSV Data Source)")

# READ: Load all incidents from CSV
datasets_df = get_datasets_from_csv()

if not datasets_df.empty:
    
    # --- Metrics Section ---
    col1, col2, col3 = st.columns(3)
    
    total_datasets = len(datasets_df)
    # Check if columns exist before filtering
    open_datasets = datasets_df[datasets_df['status'] == 'Open'].shape[0] if 'status' in datasets_df.columns else 0
    critical_datasets = datasets_df[datasets_df['severity'] == 'Critical'].shape[0] if 'severity' in datasets_df.columns else 0

    col1.metric("Total Datasets", total_datasets)
    col2.metric("Open Datasets", open_datasets)
    col3.metric("Critical Datasets", critical_datasets)

    st.markdown("---")

    # --- Charts Section ---
    st.header("Datasets Analysis")
    chart_col1, chart_col2 = st.columns(2)

    if 'severity' in datasets_df.columns:
        # Chart 1: Datasets by Severity
        severity_counts = datasets_df['severity'].value_counts().reset_index()
        severity_counts.columns = ['Severity', 'Count']
        fig_severity = px.pie(
            severity_counts, 
            values='Count', 
            names='Severity', 
            title='Datasets by Severity',
            color_discrete_sequence=px.colors.sequential.Plasma_r # Use a nice color sequence
        )
        chart_col1.plotly_chart(fig_severity, use_container_width=True)
    else:
        chart_col1.warning("Cannot plot Severity: 'severity' column missing.")

    if 'status' in datasets_df.columns:
        # Chart 2: Incidents by Status
        status_counts = datasets_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_status = px.bar(
            status_counts, 
            x='Status', 
            y='Count', 
            title='Datasets by Status',
            color='Status',
            color_discrete_map={'Open': '#EF4444', 'In Progress': '#F59E0B', 'Closed': '#10B981'},
        )
        chart_col2.plotly_chart(fig_status, use_container_width=True)
    else:
        chart_col2.warning("Cannot plot Status: 'status' column missing.")


    st.markdown("---")

    # --- Data Table Section ---
    st.header("All Incidents Data")
    # Sort by timestamp, if it exists, to show most recent incidents first
    if 'timestamp' in datasets_df.columns:
        datasets_df = datasets_df.sort_values(by='timestamp', ascending=False)
        
    st.dataframe(datasets_df, use_container_width=True, height=350)
    

# --- Sidebar Info ---
st.sidebar.header("Data Source")
st.sidebar.info("This dashboard is running in **Read-Only (CSV) mode**.")
st.sidebar.caption(f"File Path being used: `{CSV_FILE_PATH}`")