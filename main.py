import os
import streamlit as st
import pandas as pd
from io import BytesIO

# Setting up the App
st.set_page_config(page_title="Data Alchemist", page_icon="⚗️", layout="wide")
st.title("⚗️Data Alchemist - Clean, and Visualize Your Data")
st.write("Transform your files between CSV and Excel formats with built-in data cleaning and visualization!")


# File uploader with multiple file support
uploaded_files = st.file_uploader("Upload your file (CSV or Excel)", type=["csv", "xlsx"], accept_multiple_files=True)


# Define the process_file function
def process_file(file):
    file_ext = os.path.splitext(file.name)[-1].lower()

    if file_ext == ".csv":
        try:
            df = pd.read_csv(file, on_bad_lines='skip')
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")

    elif file_ext == ".xlsx":
        df = pd.read_excel(file)
    else:
        st.error(f"Unsupported file type: {file_ext}")
        return

    # Display file information
    st.write(f"**File Name:** {file.name}")
    st.write(f"**File Type:** {file_ext}")
    st.write(f"**File Size:** {file.size/1024:.2f} KB")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Preview the Head of the Dataframe:**")
    st.dataframe(df.head())

    # Options For Data Cleaning
    st.subheader("**🧹 Data Cleaning Options:**")
    if st.checkbox(f"Clean Data for {file.name}", key=f"clean_{file.name}"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Remove duplicates from {file.name}", key=f"dup_{file.name}"):
                df.drop_duplicates(inplace=True)
                st.write("Duplicate data removed!")
        with col2:
            if st.button(f"Fill Missing Values in {file.name}", key=f"fill_{file.name}"):
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                st.write("Missing values filled!")

    # Choose Specific Columns
    st.subheader("**Select Columns to Convert:**")
    columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=list(df.columns), key=f"cols_{file.name}")
    if columns:
        df = df[columns]

    # Data Visualization and Summary Options
    st.subheader("**📊 Data Visualization & Summary:**")
    if st.checkbox("Do you want to see the Visualization?", key=f"viz_{file.name}"):
        st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
        
    # Data Summary Section
    if st.checkbox(f"Do you want to see the summary for {file.name}", key=f"summary_{file.name}"):
        # Display basic statistical summary for numeric columns
        st.write("**Data Summary:**")
        st.write(df.describe())

    # Convert the file to CSV or Excel
    st.subheader("**🔄️ Conversion Options:**")
    conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel"], key=f"conv_{file.name}")
    if st.button(f"Convert {file.name}", key=f"conv_btn_{file.name}"):
        buffer = BytesIO()
        if conversion_type == "CSV":
            df.to_csv(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".csv")
            mime_type = "text/csv"
        elif conversion_type == "Excel":
            df.to_excel(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".xlsx")
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            st.error("Unsupported conversion type")
            return

        buffer.seek(0)

        # File Download Button
        st.download_button(
            label=f"⏬ Download {file.name} as {conversion_type}",
            data=buffer,
            file_name=new_file_name,
            mime=mime_type
        )

# Multiple Files Tabs, dont add duplicate file
if uploaded_files is not None and len(uploaded_files) > 0:
    # Filter out duplicate files based on file name
    unique_files_dict = {}
    for file in uploaded_files:
        if file.name not in unique_files_dict:
            unique_files_dict[file.name] = file
    unique_files = list(unique_files_dict.values())

    # If multiple unique files, display each in its own tab
    if len(unique_files) > 1:
        tabs = st.tabs([f"{file.name}" for file in unique_files])
        for tab, file in zip(tabs, unique_files):
            with tab:
                process_file(file)
    else:
        process_file(unique_files[0])