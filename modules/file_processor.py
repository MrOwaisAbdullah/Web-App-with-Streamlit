import os
import pandas as pd
import streamlit as st
from io import BytesIO
import re
import altair as alt


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
            try:
                df = pd.read_json(file)
            except ValueError as e:
                if "Trailing data" in str(e):
                    df = pd.read_json(file, lines=True)
                else:
                    st.error(f"Error reading {file.name}: {e}")
                    return None
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
    st.header("**📂 File Details:**")
    st.write(f"**File Name:** {file.name}")
    st.write(f"**File Type:** {file_ext}")
    st.write(f"**File Size:** {file.size/1024:.2f} KB")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Preview the Data (Head):**")
    st.dataframe(df.head())

    # Save summary to session_state for AI suggestions, if columns exist
    if not df.columns.empty:
        st.session_state[f"summary_{file.name}"] = df.describe().to_string()
    else:
        st.warning("The DataFrame has no columns to describe.")


    # Data Cleaning Options
    st.subheader("**🧹 Data Cleaning Options:**")
    if st.checkbox(f"Clean Data for {file.name}", key=f"clean_{sanitize_key(file.name)}"):
        col1, col2 = st.columns(2)

        # Duplicates remove button
        with col1:
            if st.button(f"Remove duplicates from {file.name}", key=f"dup_{sanitize_key(file.name)}"):
                df.drop_duplicates(inplace=True)
                st.write("Duplicate data removed!")
        
        # Missing value filling Button
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

    # Parent container for Visualization and Filtering
    st.subheader("**📊 Visualization & Data Filtering:**")
    viz_mode = st.radio("Choose visualization mode:", ["Default Bar Chart", "Custom Chart & Filtering"], key=f"viz_mode_{sanitize_key(file.name)}")
    
    if viz_mode == "Default Bar Chart":
        try:
            st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
        except Exception as e:
            st.error(f"Error creating bar chart: {e}")
    else:
        # Custom Chart Section
        numeric_columns = df.select_dtypes(include='number').columns.tolist()
        if numeric_columns:
            selected_col = st.selectbox("Select a numeric column for a custom line chart", numeric_columns, key=f"chart_{sanitize_key(file.name)}")
            chart = alt.Chart(df.reset_index()).mark_line().encode(
                x=alt.X("index:O", title="Row Index"),
                y=alt.Y(f"{selected_col}:Q", title=selected_col)
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No numeric columns available for custom charts.")
        
        # Data Filtering Section
        with st.expander("Data Filtering Options"):
            filters = {}
            for col in numeric_columns:
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                filters[col] = st.slider(f"Filter {col}", min_value=min_val, max_value=max_val, value=(min_val, max_val), key=f"filter_{sanitize_key(col)}")
            filtered_df = df.copy()
            for col, (min_val, max_val) in filters.items():
                filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]
            st.write("**Filtered Data Preview:**")
            st.dataframe(filtered_df.head())

    # Conversion Options
    st.subheader("**🔄 Conversion Options:**")
    conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel", "JSON"], key=f"conv_{sanitize_key(file.name)}")
    if st.button(f"Convert {file.name}", key=f"conv_btn_{sanitize_key(file.name)}"):
        buffer = BytesIO()
        # Convert to CSV
        if conversion_type == "CSV":
            df.to_csv(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".csv")
            mime_type = "text/csv"

        # Convert to Excel
        elif conversion_type == "Excel":
            df.to_excel(buffer, index=False)
            new_file_name = file.name.replace(file_ext, ".xlsx")
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Convert to Json
        elif conversion_type == "JSON":
            json_str = df.to_json(orient='records', lines=True)
            buffer.write(json_str.encode('utf-8'))
            new_file_name = file.name.replace(file_ext, ".json")
            mime_type = "application/json"
        else:
            st.error("Unsupported conversion type")
            return
        buffer.seek(0)

        # Download Button
        st.download_button(
            label=f"⏬ Download {file.name} as {conversion_type}",
            data=buffer,
            file_name=new_file_name,
            mime=mime_type
        )
    return df
