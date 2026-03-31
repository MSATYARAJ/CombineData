import streamlit as st
import pandas as pd
import io
from python_calamine import CalamineWorkbook

# Ensure xlsxwriter is installed for Excel export
from xlsxwriter import Workbook

st.set_page_config(page_title="Universal Data Merger", layout="wide")

@st.cache_data(show_spinner="Loading data...")
def load_data(uploaded_file):
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.csv'): return pd.read_csv(uploaded_file)
        elif name.endswith(('.xlsx', '.xlsm')): return pd.read_excel(uploaded_file, engine='calamine')
        elif name.endswith('.parquet'): return pd.read_parquet(uploaded_file)
        return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

st.title("🚀 Advanced Multi-Key Merger")

col_a, col_b = st.columns(2)
with col_a:
    file1 = st.file_uploader("Main Table", type=None)
with col_b:
    file2 = st.file_uploader("Table to Join", type=None)

if file1 and file2:
    df1 = load_data(file1)
    df2 = load_data(file2)
    
    if df1 is not None and df2 is not None:
        a, b = st.columns(2)
        with a: 
            st.write("### Main Table Preview")
            st.dataframe(df1.head(5))
        with b: 
            st.write("### Join Table Preview")
            st.dataframe(df2.head(5))

        st.divider()
        st.subheader("🛠 Join Configuration")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            left_keys = st.multiselect("Key Column(s) (Main Table)", df1.columns)
        with c2:
            right_keys = st.multiselect("Key Column(s) (Second Table)", df2.columns)
        with c3:
            join_type = st.selectbox("Join Type", ["left", "right", "inner", "outer"])

        # NEW: Suffix Configuration
        st.write("#### Handle Overlapping Column Names")
        s1, s2 = st.columns(2)
        suffix_left = s1.text_input("Suffix for Main Table", "_left")
        suffix_right = s2.text_input("Suffix for Second Table", "_right")

        # Column selection
        other_cols = [c for c in df2.columns if c not in right_keys]
        selected_cols = st.multiselect("Additional columns to pull from Second Table", other_cols, default=other_cols)

        if len(left_keys) != len(right_keys):
            st.warning("⚠️ Select the same number of keys for both tables.")
        elif len(left_keys) == 0:
            st.info("Select at least one key column to begin.")
        else:
            if st.button("🚀 Merge Datasets"):
                cols_to_use = list(right_keys) + list(selected_cols)
                
                # Perform the join with custom suffixes
                result = pd.merge(
                    df1, 
                    df2[cols_to_use], 
                    left_on=left_keys, 
                    right_on=right_keys, 
                    how=join_type,
                    suffixes=(suffix_left, suffix_right) # Applied suffixes here
                )
    
                st.success(f"Merged successfully! Row count: {len(result)}")
                st.dataframe(result.head(100))

                st.divider()
                st.subheader("📥 Export Result")
    
                d_col1, d_col2 = st.columns(2)

                # CSV Download
                csv_buffer = io.BytesIO()
                result.to_csv(csv_buffer, index=False)
                d_col1.download_button("Download as CSV", csv_buffer.getvalue(), "merged.csv", "text/csv", use_container_width=True)

                # Excel Download
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    result.to_excel(writer, index=False, sheet_name='MergedData')
                d_col2.download_button("Download as Excel", excel_buffer.getvalue(), "merged.xlsx", "application/vnd.ms-excel", use_container_width=True)
