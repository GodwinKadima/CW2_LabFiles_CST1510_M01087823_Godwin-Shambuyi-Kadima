import streamlit as st
import pandas as pd
import requests # Required for direct API calls
import json     # Required for formatting JSON payload
import time     # Required for handling retries
from typing import Optional

# Import the Database Manager
from services.database_manager import DatabaseManager


# --- API CONFIGURATION (AS REQUESTED) ---
# 🚨 SECURITY RISK: This key is hardcoded. Use st.secrets instead!
API_KEY = "" 
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# Using the existing model that works with the OpenAI API
OPENAI_MODEL = "gpt-4o-mini" # Corrected from gpt-4.1-mini
MAX_RETRIES = 3

# --- PLATFORM CONFIGURATION ---
db = DatabaseManager("intelligence_platform.db")

# Configurations for all three domains
DOMAIN_CONFIGS = {
    "Cybersecurity Incidents": {
        "icon": "🛡️",
        "table": "security_incidents",
        "fields": "id, incident_type, severity, status, timestamp",
        "prompt": "You are a Cyber Incident Analyst. Analyze the provided security incident data. Summarize the status of incidents, identify the highest severity type, and suggest next steps to mitigate the top risk.",
    },
    "IT Operations Tickets": {
        "icon": "💻",
        "table": "it_tickets",
        "fields": "id, title, priority, status, assigned_to, timestamp",
        "prompt": "You are an IT Support Manager. Analyze the provided IT ticket data. Determine the most critical priority tickets currently open, identify which team member is overloaded, and recommend a re-prioritization strategy.",
    },
    "Data Science Experiments": {
        "icon": "📊",
        "table": "ml_experiments",
        "fields": "id, model_name, dataset, accuracy, run_time_seconds, status, timestamp",
        "prompt": "You are a Machine Learning Scientist. Analyze the experiment data provided. Identify the highest performing model (by accuracy), the average run time, and suggest potential models that should be retired or re-run for optimization.",
    },
}
# --- HELPER FUNCTIONS ---

@st.cache_data(ttl=60)
def fetch_data_for_domain(domain_key: str) -> Optional[pd.DataFrame]:
    """Fetches the data required by the selected domain from the database."""
    config = DOMAIN_CONFIGS.get(domain_key)
    if not config:
        return pd.DataFrame()

    query = f"SELECT {config['fields']} FROM {config['table']} ORDER BY timestamp DESC LIMIT 500"
    data = db.fetch_all(query)
    
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()


def get_ai_response(prompt, history, system_instruction):
    """Sends the user's prompt and chat history to the OpenAI API using requests."""
    
    contents = []
    # Build the conversation history
    for msg in history:
        contents.append({"role": msg["role"], "content": msg["content"]})
        
    # Append the current user prompt
    contents.append({"role": "user", "content": prompt})

    payload_data = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            *contents # The full conversation history
        ]
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                OPENAI_API_URL, 
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {API_KEY}'
                }, 
                data=json.dumps(payload_data)
            )
            response.raise_for_status() 
            
            result = response.json()
            
            # Extract the generated text from the structured JSON response
            generated_text = result.get('choices', [{}])[0].get('message', {}).get('content')
            
            return generated_text if generated_text else "I couldn't generate a clear response for that request."
            
        except requests.exceptions.RequestException as e:
            if response.status_code == 401:
                return "Authentication Error: The hardcoded API Key is invalid or expired."
            
            # Log the connection error
            st.error(f"Connection Error: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time) 
            else:
                return "Failed to get a response after several tries. Check your connection or API status."
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            return "An internal error occurred."
    return "Error: Could not retrieve response." # Fallback

def initialize_ai_state(domain_key: str):
    """Initializes chat history and loads data context."""
    st.session_state['messages'] = []
    
    config = DOMAIN_CONFIGS[domain_key]
    df = fetch_data_for_domain(domain_key)
    
    context_message = ""
    if df.empty:
        context_message = f"I am ready to assist you. However, the **{domain_key}** table is currently empty."
    else:
        # Pass the data as a string for the AI to analyze
        data_string = df.to_string(index=False)
        context_message = (
            f"I am now configured as the **{domain_key}** Analyst. "
            f"I have loaded the following data for my analysis:\n\n---\n{data_string}\n---\n\n"
            f"What is your first question or request regarding this data?"
        )
    
    st.session_state['messages'].append({"role": "assistant", "content": context_message})

def clear_chat_history():
    """Resets the chat by re-initializing the state for the current domain."""
    initialize_ai_state(st.session_state.current_domain)
    st.rerun()


# --- AUTHENTICATION CHECK ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("You must be logged in to view the AI Assistant.")
    st.stop()


# --- MAIN PAGE LAYOUT ---

st.title("💡 Multi-Domain Intelligence Assistant")
st.success(f"Hello, **{st.session_state.username}**! Use the specialized AI to analyze your domain data.")

# --- SIDEBAR CONFIGURATION (The Domain Switcher) ---

with st.sidebar:
    st.header("Assistant Settings")
    
    # 1. Domain Selection
    domain_keys = list(DOMAIN_CONFIGS.keys())
    
    if 'current_domain' not in st.session_state:
        st.session_state.current_domain = domain_keys[0] 
        
    selected_domain = st.selectbox(
        "Select Domain Assistant:", 
        options=domain_keys, 
        key='domain_select',
        index=domain_keys.index(st.session_state.current_domain)
    )

    # Logic to re-initialize state if domain changes or on first load
    if selected_domain != st.session_state.current_domain or 'messages' not in st.session_state:
        st.session_state.current_domain = selected_domain
        initialize_ai_state(selected_domain)
        st.toast(f"Assistant switched to {selected_domain}!")
        st.rerun() 

    # 2. Clear History Button
    st.markdown("---")
    if st.button("🗑️ Start New Chat", help="Starts a fresh conversation for the selected domain."):
        clear_chat_history()


# --- CHAT INTERFACE ---

current_config = DOMAIN_CONFIGS[st.session_state.current_domain]
st.header(f"{current_config['icon']} {st.session_state.current_domain} Analyst")
st.markdown("---")

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask a question about your data..."):
    # 1. Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Get AI response and display it
    with st.chat_message("assistant"):
        with st.spinner("AI is thinking and analyzing the data..."):
            
            system_prompt = DOMAIN_CONFIGS[st.session_state.current_domain]["prompt"]
            
            # Call the API function using the user's hardcoded key and requests logic
            assistant_response = get_ai_response(
                prompt, 
                st.session_state.messages, 
                system_prompt
            )
            
            # Display the response
            st.markdown(assistant_response)

    # 3. Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})