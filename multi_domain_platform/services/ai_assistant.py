import streamlit as st
from openai import OpenAI
from typing import List, Dict

# 🚨 IMPORTANT: Replace this placeholder with your actual, new OpenAI API Key.
# We are hardcoding it here to simplify the setup as requested.
HARDCODED_API_KEY = "" 

class AIAssistant:
    """
    Wrapper around the OpenAI chat model for conversation management.
    Handles API communication and conversation history.
    """
    
    def __init__(self, system_prompt: str = "You are a helpful analyst."):
        self._system_prompt = system_prompt
        
        # 1. Initialize the OpenAI client using the hardcoded key
        try:
            self._client = OpenAI(api_key=HARDCODED_API_KEY)
            self._is_ready = True
        except Exception:
            self._client = None
            self._is_ready = False
            
        self._history: List[Dict[str, str]] = []

    def clear_history(self):
        """Clears the conversation history."""
        self._history.clear()

    def send_message(self, user_message: str):
        """Send a message to the OpenAI API and get a real response."""
        
        # 1. Add the new user message to the history
        self._history.append({"role": "user", "content": user_message})

        if not self._is_ready:
            response = "[API ERROR]: The OpenAI Client failed to initialize. Check the hardcoded API key is correct."
            self._history.append({"role": "assistant", "content": response})
            return response

        # 2. Build the full message list for the API call (System Prompt + History)
        messages = [{"role": "system", "content": self._system_prompt}] + self._history

        try:
            # 3. Call the OpenAI API using the official client
            completion = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7 
            )
            
            # 4. Extract and store the response content
            assistant_response = completion.choices[0].message.content
            self._history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
        
        except Exception as e:
            error_msg = f"An API error occurred: {e}"
            self._history.append({"role": "assistant", "content": error_msg})
            return error_msg