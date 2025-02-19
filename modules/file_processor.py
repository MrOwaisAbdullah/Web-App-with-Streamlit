import os
import pandas as pd
import streamlit as st
from io import BytesIO
import re

def sanitize_key(file_name: str) -> str:
    # Replace any non-alphanumeric character with an underscore
    return re.sub(r'\W+', '_', file_name)

def read_file(file):
    file_ext = os.path.splitext(file.name)[-1].lower()
    try:
        if file_ext == ".csv":
            df = pd.read_csv(file, on_bad_lines='skip')
        elif file_ext == ".xlsx":
            df = pd.read_excel(file)
        elif file_ext == ".json":
            df = pd.read_json(file)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            return None
    except Exception as e:
        st.error(f"Error reading {file.name}: {e}")
        return None
    return df

def process_file(file):
    df = read_file(file)
    if df is None:
        return None
    
    file_ext = os.path.splitext(file.name)[-1].lower()

    # Display file info
    st.write(f"**File Name:** {file.name}")
    st.write(f"**File Type:** {file_ext}")
    st.write(f"**File Size:** {file.size/1024:.2f} KB")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Preview the Data (Head):**")
    st.dataframe(df.head())

    # Save summary to session_state for AI suggestions
    st.session_state[f"summary_{file.name}"] = df.describe().to_string()

    # Data Cleaning Options
    st.subheader("**🧹 Data Cleaning Options:**")
    if st.checkbox(f"Clean Data for {file.name}", key=f"clean_{sanitize_key(file.name)}"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Remove duplicates from {file.name}", key=f"dup_{sanitize_key(file.name)}"):
                df.drop_duplicates(inplace=True)
                st.write("Duplicate data removed!")
        with col2:
            if st.button(f"Fill Missing Values in {file.name}", key=f"fill_{sanitize_key(file.name)}"):
                numeric_cols = df.select_dtypes(include=['number']).columns
                df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
                st.write("Missing values filled!")

    # Select Columns
    st.subheader("**Select Columns to Convert:**")
    columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=list(df.columns), key=f"cols_{sanitize_key(file.name)}")
    if columns:
        df = df[columns]

    # Visualization & Summary Options
    st.subheader("**📊 Data Visualization & Summary:**")
    if st.checkbox("Show Visualization", key=f"viz_{sanitize_key(file.name)}"):
        try:
            st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
        except Exception as e:
            st.error(f"Error creating chart: {e}")
    if st.checkbox(f"Show Summary for {file.name}", key=f"summary_{sanitize_key(file.name)}"):
        st.write("**Data Summary:**")
        st.write(df.describe())

    # Conversion Options
    st.subheader("**🔄 Conversion Options:**")
    conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel", "JSON"], key=f"conv_{sanitize_key(file.name)}")
    if st.button(f"Convert {file.name}", key=f"conv_btn_{sanitize_key(file.name)}"):
        buffer = BytesIO()
        if conversion_type == "CSV":
            df.to_csv(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".csv")
            mime_type = "text/csv"
        elif conversion_type == "Excel":
            df.to_excel(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".xlsx")
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif conversion_type == "JSON":
            json_str = df.to_json(orient='records', lines=True)
            buffer.write(json_str.encode('utf-8'))
            new_file_name = file.name.replace(file_ext, ".json")
            mime_type = "application/json"
        else:
            st.error("Unsupported conversion type")
            return
        buffer.seek(0)
        st.download_button(
            label=f"⏬ Download {file.name} as {conversion_type}",
            data=buffer,
            file_name=new_file_name,
            mime=mime_type
        )
    return df
