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
    # Read file content as a string
    content = file.getvalue().decode("utf-8", errors="replace")
    if len(content.strip()) == 0:
        st.error(f"File {file.name} is empty.")
        return None
    try:
        if file_ext == ".csv":
            file.seek(0)
            # Try reading the CSV using a common encoding
            df = pd.read_csv(file, encoding="utf-8-sig", on_bad_lines='skip')
            # If no columns are found, try forcing header=None
            if df.empty or df.columns.size == 0:
                file.seek(0)
                df = pd.read_csv(file, encoding="utf-8-sig", header=None, on_bad_lines='skip')
                if df.empty or df.columns.size == 0:
                    st.error(f"No columns to parse from file {file.name}.")
                    return None
        elif file_ext == ".xlsx":
            file.seek(0)
            df = pd.read_excel(file)
        elif file_ext == ".json":
            file.seek(0)
            try:
                df = pd.read_json(file)
            except ValueError as e:
                if "Trailing data" in str(e):
                    file.seek(0)
                    df = pd.read_json(file, lines=True)
                else:
                    st.error(f"Error reading {file.name}: {e}")
                    return None
        else:
            st.error(f"Unsupported file type: {file_ext}")
            return None
    except (ValueError, TypeError) as e:
        st.error(f"Error reading {file.name}: {e}")
        return None
    return df


def process_file(file, new_name):
    df = read_file(file)
    if df is None:
        return None
    
    file_ext = os.path.splitext(file.name)[-1].lower()

    # Use the renamed file for display
    st.write(f"**File Name:** {new_name}")
    st.write(f"**File Type:** {file_ext}")
    st.write(f"**File Size:** {file.size/1024:.2f} KB")
    st.write(f"**Number of Rows:** {df.shape[0]}")
    st.write(f"**Number of Columns:** {df.shape[1]}")
    st.write("**Data Preview:**")
    st.dataframe(df)

    st.session_state[f"summary_{file.name}"] = df.describe().to_string()

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
    # Define numeric_columns regardless of visualization mode
    numeric_columns = df.select_dtypes(include='number').columns.tolist()
    viz_mode = st.radio(
        "Choose visualization mode:",
        ["Default Bar Chart", "Custom Chart & Filtering"],
        key=f"viz_mode_{sanitize_key(file.name)}"
    )

    if viz_mode == "Default Bar Chart":
        try:
            st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
        except (ValueError, TypeError) as e:
            st.error(f"Error creating bar chart: {e}")
    else:
        if numeric_columns:
            selected_col = st.selectbox(
                "Select a numeric column for a custom line chart",
                numeric_columns,
                key=f"chart_{sanitize_key(file.name)}"
            )
            chart = alt.Chart(df.reset_index()).mark_line().encode(
                x=alt.X("index:O", title="Row Index"),
                y=alt.Y(f"{selected_col}:Q", title=selected_col)
            ).interactive()
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("No numeric columns available for custom charts.")

        # Data Filtering Section
        with st.expander("Data Filtering Options"):
            if numeric_columns:
                filters = {}
                for col in numeric_columns:
                    min_val = float(df[col].min())
                    max_val = float(df[col].max())
                    if min_val == max_val:
                        st.write(f"{col}: Single value {min_val} (No filtering needed)")
                        filters[col] = (min_val, max_val)
                    else:
                        filters[col] = st.slider(
                            f"Filter {col}",
                            min_value=min_val,
                            max_value=max_val,
                            value=(min_val, max_val),
                            key=f"filter_{sanitize_key(file.name)}_{sanitize_key(col)}"
                        )
                filtered_df = df.copy()
                for col, (min_val, max_val) in filters.items():
                    filtered_df = filtered_df[(filtered_df[col] >= min_val) & (filtered_df[col] <= max_val)]
                st.write("**Filtered Data Preview:**")
                st.dataframe(filtered_df.head())
            else:
                st.write("No numeric columns available for filtering.")


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
