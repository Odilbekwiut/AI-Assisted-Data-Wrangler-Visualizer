import streamlit as st

# NEW — import the session state functions from our utils folder
from utils.session_state import initialize_session_state, reset_session_state, data_is_loaded

# --- Page Configuration ---
st.set_page_config(
    page_title="AI-Assisted Data Wrangler & Visualizer",
    layout="wide"
)

# NEW — Initialize session state every time the app starts or reruns
# This is safe to call repeatedly — it only sets keys that don't exist yet
initialize_session_state()

# --- App Title and Welcome Message ---
st.title("AI-Assisted Data Wrangler & Visualizer")

st.write(
    "Welcome! This app helps you upload, clean, visualize, and export datasets "
    "using an interactive step-by-step workflow."
)

# --- Under Development Notice ---
st.info("This app is currently under development. Features will be added step by step.")

st.divider()

# --- How to Use This App ---
st.subheader("What This App Does")

st.write(
    "This app helps you upload, clean, visualize, and export datasets "
    "through a simple step-by-step workflow. "
    "No coding required — everything is point and click."
)

st.subheader("The 4 Pages")

st.markdown("""
| Page | What it does |
|---|---|
| 📁 **Upload & Overview** | Upload your CSV, XLSX, or JSON file and see an instant summary of your data |
| 🧹 **Cleaning & Preparation** | Fix missing values, remove duplicates, convert types, clean text, scale numbers, and more |
| 📊 **Visualization Builder** | Build charts from your cleaned data — histogram, bar, line, scatter, box, and pie |
| 💾 **Export & Report** | Download your cleaned dataset and a full transformation report |
""")

st.subheader("Basic Workflow")

st.markdown("""
1. **Upload** your dataset on the Upload & Overview page
2. **Clean** and prepare your data on the Cleaning & Preparation page
3. **Visualize** your data on the Visualization Builder page
4. **Export** your cleaned data and report on the Export & Report page
""")

st.info(
    "Tip: Use the **sidebar** at any time to reset your session, "
    "reset to original data, or undo your last cleaning action."
)

# --- Sidebar ---
st.sidebar.title("Navigation")
st.sidebar.markdown(
    """
    This app contains **4 pages**:

    1. Upload & Overview
    2. Cleaning & Preparation
    3. Visualization Builder
    4. Export & Report
    """
)

# Undo last action — only show if data is loaded
if data_is_loaded():
    st.sidebar.divider()
    if st.session_state.get("undo_stack") is not None:
        if st.sidebar.button("↩ Undo Last Action", key="btn_undo"):
            st.session_state.working_df = st.session_state.undo_stack.copy()
            st.session_state.undo_stack = None
            st.session_state.transformation_log.append({
                "operation": "undo_last_action",
                "columns": [],
                "parameters": {},
                "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
    else:
        st.sidebar.button("↩ Undo Last Action", disabled=True, key="btn_undo")

# Reset working data button — only show if data is loaded
if data_is_loaded():
    st.sidebar.divider()
    if st.sidebar.button("🔄 Reset to Original Data", key="btn_reset_to_original"):
        st.session_state.working_df = st.session_state.original_df.copy()
        st.session_state.undo_stack = None
        st.session_state.transformation_log.append({
            "operation": "reset_to_original",
            "columns": [],
            "parameters": {"note": "Working data reset to original uploaded dataset"},
            "timestamp": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.rerun()


# NEW — Reset Session button in the sidebar
st.sidebar.divider()  # A thin line to separate navigation from the button

if st.sidebar.button("Reset Session"):
    reset_session_state()       # Clear all session state values
    st.rerun()                  # Rerun the app so the cleared state takes effect
    
st.divider()

# --- Quick Navigation ---
st.subheader("Quick Navigation")
st.write("Select a page from the **sidebar on the left** to get started.")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        **📁 Upload & Overview**
        Upload your CSV, XLSX, or JSON file.
        See shape, column types, missing values,
        duplicates, and statistics instantly.
        """
    )
    st.markdown(
        """
        **📊 Visualization Builder**
        Build charts from your cleaned data.
        Histogram, bar, line, scatter, box,
        and pie charts with download support.
        """
    )

with col2:
    st.markdown(
        """
        **🧹 Cleaning & Preparation**
        Fix missing values, remove duplicates,
        convert types, scale numbers, clean text,
        and track every change in a log.
        """
    )
    st.markdown(
        """
        **💾 Export & Report**
        Download your cleaned dataset as CSV,
        Excel, or JSON. Export a full
        transformation report as a TXT file.
        """
    )