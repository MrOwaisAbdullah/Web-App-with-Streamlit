import os
import streamlit as st
from modules.file_processor import process_file
from modules.ai_integration import get_ai_suggestions
import re

# App configuration
st.set_page_config(page_title="AI Data Alchemist", page_icon="⚗️", layout="wide")
st.title("⚗️ AI Data Alchemist - Clean, Transform & Visualize Your Data")
st.write("Transform your files between CSV, Excel, and JSON formats with built-in cleaning, visualization, and AI-powered suggestions.")

def sanitize_key(file_name: str) -> str:
    # Replace any non-alphanumeric character with an underscore
    return re.sub(r'\W+', '_', file_name)

# File uploader with multiple file support
uploaded_files = st.file_uploader(
    "Upload your file (CSV, Excel, JSON)",
    type=["csv", "xlsx", "json"],
    accept_multiple_files=True
)

if uploaded_files:
    # Filter duplicate files by name
    unique_files = list({file.name: file for file in uploaded_files}.values())
    
    # If multiple files, create tabs, otherwise process directly
    if len(unique_files) > 1:
        tabs = st.tabs([file.name for file in unique_files])
        for tab, file in zip(tabs, unique_files):
            with tab:
                # Get AI suggestions if a summary is available
                if st.button("🤖 Get AI Cleaning Suggestions", key=f"sugg_{sanitize_key(file.name)}"):
                    with st.spinner("Generating suggestions...", show_time=True):
                        data_summary = st.session_state.get(f"summary_{file.name}", "")
                        if data_summary:
                            suggestions = get_ai_suggestions(data_summary)
                        else:
                            suggestions = "No data summary available."
                    
                        st.expander("AI Cleaning Suggestions", expanded=True).write(suggestions)
                df = process_file(file)



    else:
        file = list(unique_files)[0]
        if st.button("🤖 Get AI Cleaning Suggestions", key=f"sugg_{sanitize_key(file.name)}"):
            with st.spinner("Generating suggestions...", show_time=True):
                suggestions = get_ai_suggestions(st.session_state[f"summary_{file.name}"])
                st.expander("AI Cleaning Suggestions", expanded=True).write(suggestions)

        df = process_file(file)

