import streamlit as st

from utils.session_state import initialize_session_state, data_is_loaded
from utils.file_handlers import load_uploaded_file
from utils.profiling import (
    get_shape_info,
    get_column_dtype_summary,
    get_missing_values_summary,
    get_duplicate_count,
    get_numeric_summary,
    get_categorical_summary
)

# Always initialize session state at the top of every page
initialize_session_state()

# --- Page Title and Description ---
st.title("Upload & Overview")

st.write(
    "Upload your dataset here to get started. "
    "Supported formats are CSV, XLSX, and JSON. "
    "Once loaded, you will see a basic overview of your data."
)

st.divider()

# --- Current Dataset Summary ---
if data_is_loaded():
    _df = st.session_state.working_df
    _numeric = _df.select_dtypes(include=["number"]).shape[1]
    _categorical = _df.select_dtypes(include=["object", "category"]).shape[1]

    with st.container():
        st.markdown("### 📊 Current Dataset Summary")

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("File", st.session_state.uploaded_file_name or "Unknown")
        col2.metric("Rows", _df.shape[0])
        col3.metric("Columns", _df.shape[1])
        col4.metric("Numeric", _numeric)
        col5.metric("Categorical", _categorical)
        col6.metric("Transformations", len(st.session_state.transformation_log))

    st.divider()

else:
    st.info("No dataset loaded yet. Upload a file below to get started.")
    st.divider()

# --- File Uploader ---
uploaded_file = st.file_uploader(
    label="Choose a file to upload",
    type=["csv", "xlsx", "json"],
    key="file_uploader"
)

# --- Determine which dataframe to show ---
# There are three possible situations:
#
# 1. The user has just uploaded a new file → load it fresh
# 2. The uploader looks empty but data is already in session state → use session data
# 3. Nothing uploaded and no session data → show a friendly prompt

if uploaded_file is not None:

    # Situation 1 — a file is currently in the uploader
    # Only reload if it is a different file from what is already stored
    if uploaded_file.name != st.session_state.uploaded_file_name:

        df, file_type, error_message = load_uploaded_file(uploaded_file)

        if error_message:
            st.error(f"Error loading file: {error_message}")
            st.stop()

        # Save everything into session state
        st.session_state.original_df = df.copy()
        st.session_state.working_df = df.copy()
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_type = file_type
        st.session_state.data_loaded = True

        st.success("File loaded successfully!")

elif data_is_loaded():

    # Situation 2 — uploader is empty but data exists in session state
    # This happens when the user navigates away and comes back
    st.info(
        "A dataset is already loaded in this session. "
        "You can upload a new file above to replace it."
    )

else:

    # Situation 3 — nothing uploaded and no data in session
    st.info("Please upload a CSV, XLSX, or JSON file above to get started.")
    st.stop()  # Nothing to show below — stop here cleanly

# --- Everything below runs for Situation 1 and Situation 2 ---
# At this point we know data_is_loaded() is True

df = st.session_state.working_df  # shortcut to avoid repeating long names

# ---- Section 1: File Information ----
st.subheader("File Information")

rows, columns = get_shape_info(df)

col1, col2, col3 = st.columns(3)
col1.metric("File Name", st.session_state.uploaded_file_name)
col2.metric("File Type", st.session_state.uploaded_file_type.upper())
col3.metric("Shape", f"{rows} rows × {columns} columns")

st.divider()

# ---- Section 2: Data Preview ----
st.subheader("Data Preview (First 5 Rows)")
st.dataframe(df.head(), use_container_width=True)

st.divider()

# ---- Section 3: Column and Data Type Summary ----
st.subheader("Column & Data Type Summary")
st.write(
    f"Your dataset has **{columns} columns**. "
    "Here is the data type pandas has assigned to each one."
)
dtype_summary = get_column_dtype_summary(df)
st.dataframe(dtype_summary, use_container_width=True)

st.divider()

# ---- Section 4: Missing Values Summary ----
st.subheader("Missing Values Summary")
missing_summary = get_missing_values_summary(df)

if missing_summary.empty:
    st.success("No missing values found in this dataset.")
else:
    st.warning(
        f"Missing values detected in {len(missing_summary)} column(s). "
        "See details below."
    )
    st.dataframe(missing_summary, use_container_width=True)

st.divider()

# ---- Section 5: Duplicate Rows ----
st.subheader("Duplicate Rows")
duplicate_count = get_duplicate_count(df)

if duplicate_count == 0:
    st.success("No duplicate rows found in this dataset.")
else:
    st.warning(
        f"Found **{duplicate_count}** duplicate row(s). "
        "You can remove these in the Cleaning & Preparation page."
    )

st.divider()

# ---- Section 6: Numeric Summary ----
st.subheader("Numeric Summary")
st.write(
    "Descriptive statistics for all numeric columns. "
    "Each row below represents one numeric column from your dataset."
)
numeric_summary = get_numeric_summary(df)

if numeric_summary.empty:
    st.info("No numeric columns found in the current dataset.")
else:
    st.dataframe(numeric_summary, use_container_width=True)

st.divider()

# ---- Section 7: Categorical Summary ----
st.subheader("Categorical Summary")
st.write(
    "Summary of text and category columns. "
    "Shows how many unique values exist and which value appears most often."
)
categorical_summary = get_categorical_summary(df)

if categorical_summary.empty:
    st.info("No categorical columns found in the current dataset.")
else:
    st.dataframe(categorical_summary, use_container_width=True)