import streamlit as st
from modules.file_processor import process_file, read_file
from modules.ai_integration import get_ai_suggestions
import re

# Page Configuration
st.set_page_config(page_title="AI Data Alchemist", page_icon="⚗️", layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>⚗️ AI Data Alchemist \n\n Clean, Transform & Visualize Your Data</h1>",
    unsafe_allow_html=True
    )
st.markdown(
    "<p style='text-align: center;'>Transform your files between CSV, Excel, and JSON formats with built-in cleaning, visualization, and AI-powered suggestions.</p>",
    unsafe_allow_html=True
    )

# Initialize Session State for Renaming and Removed Files
if "rename_mapping" not in st.session_state or not isinstance(st.session_state["rename_mapping"], dict):
    st.session_state["rename_mapping"] = {}
if "removed_files" not in st.session_state or not isinstance(st.session_state["removed_files"], dict):
    st.session_state["removed_files"] = {}
if "rename_mode" not in st.session_state or not isinstance(st.session_state["rename_mode"], dict):
    st.session_state["rename_mode"] = {}

# Function to Replace any non-alphanumeric character with an underscore
def sanitize_key(file_name: str) -> str:
    return re.sub(r'\W+', '_', file_name)

# Sidebar: Upload & Display Uploaded Files & Renaming Options
with st.sidebar:
    st.markdown(
    "<h1 style='text-align: center;'>⚗️ AI Data Alchemist</h1>",
    unsafe_allow_html=True
    )

    # File uploader with multiple file support
    uploaded_files = st.file_uploader(
        "Upload your file (CSV, Excel, JSON)",
        type=["csv", "xlsx", "json"],
        accept_multiple_files=True
    )
    st.header("Uploaded Files")
    if uploaded_files:
        for file in uploaded_files:
            # Skip files marked as removed
            if st.session_state["removed_files"].get(file.name, False):
                continue

            key_base = sanitize_key(file.name)
            # Set initial rename mode to False if not already set
            if key_base not in st.session_state["rename_mode"]:
                st.session_state["rename_mode"][key_base] = False

            col1, col2 = st.columns([3, 1])
            # If in renaming mode, show a text input and save button
            if st.session_state["rename_mode"][key_base]:
                new_name = col1.text_input("Rename", value=st.session_state["rename_mapping"].get(file.name, file.name), key=f"rename_input_{key_base}")
                if col2.button("Save", key=f"save_{key_base}"):
                    st.session_state["rename_mapping"][file.name] = new_name
                    st.session_state["rename_mode"][key_base] = False
                    st.success(f"Renamed to {new_name}")
            else:
                # Show file name and a pencil button to toggle renaming
                col1.write(st.session_state["rename_mapping"].get(file.name, file.name))
                if col2.button("✏️", key=f"rename_btn_{key_base}"):
                    st.session_state["rename_mode"][key_base] = True

    else:
        st.info("No files uploaded yet.")
    
    st.markdown("---")
    st.markdown("### Developed with ❤️ by **Owais Abdullah**")
    st.markdown("**Email:** mrowaisabdullah@gmail.com")
    st.markdown("**LinkedIn:** [@mrowaisabdullah](https://www.linkedin.com/in/mrowaisabdullah/)")


# Main Section: Process Uploaded Files
if uploaded_files:
    # Filter out removed files using session_state
    unique_files = list({
        file.name: file 
        for file in uploaded_files 
        if not st.session_state["removed_files"].get(file.name, False)
    }.values())
    
    # Use rename mapping from session_state (default to original name)
    rename_mapping = st.session_state.get("rename_mapping", {})

    if not unique_files:
        st.info("No files available for processing. Please upload new files or check your removal selections.")
    elif len(unique_files) > 1:
        tabs = st.tabs([rename_mapping.get(file.name, file.name) for file in unique_files])
        for tab, file in zip(tabs, unique_files):
            with tab:
                # Compute Summary
                df_temp = read_file(file)
                if df_temp is None:
                    st.error("Error processing file.")
                else:
                    # Save summary if not already set
                    if not st.session_state.get(f"summary_{file.name}"):
                        st.session_state[f"summary_{file.name}"] = df_temp.describe().to_string()
                    
                    # Display AI Suggestion
                    if st.button("🤖 Get AI Cleaning Suggestions", key=f"sugg_{sanitize_key(file.name)}"):
                        with st.spinner("Generating suggestions...", show_time=True):
                            data_summary = st.session_state.get(f"summary_{file.name}", "")
                            if data_summary:
                                suggestions = get_ai_suggestions(data_summary)
                            else:
                                suggestions = "No data summary available."
                        st.expander("AI Cleaning Suggestions", expanded=True).write(suggestions)
                    
                    # Process the File Fully
                    process_file(file, rename_mapping.get(file.name, file.name))
    else:
        file = unique_files[0]
        df_temp = read_file(file)
        if df_temp is None:
            st.error("Error processing file.")
        else:
            if not st.session_state.get(f"summary_{file.name}"):
                st.session_state[f"summary_{file.name}"] = df_temp.describe().to_string()
            # AI Suggestion Button
            if st.button("🤖 Get AI Cleaning Suggestions", key=f"sugg_{sanitize_key(file.name)}"):
                with st.spinner("Generating suggestions...", show_time=True):
                    data_summary = st.session_state.get(f"summary_{file.name}", "")
                    if data_summary:
                        suggestions = get_ai_suggestions(data_summary)
                    else:
                        suggestions = "No data summary available."
                st.expander("AI Cleaning Suggestions", expanded=True).write(suggestions)
            process_file(file, rename_mapping.get(file.name, file.name))
else:
    st.markdown(
    "<p style='text-align: center; background-color: rgba(46, 204, 113, 0.3); padding: 10px; border-radius: 5px;'>Please upload a file to get started.</p>",
    unsafe_allow_html=True
    )

