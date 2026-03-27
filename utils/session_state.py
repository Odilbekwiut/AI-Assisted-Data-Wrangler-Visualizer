import streamlit as st


def initialize_session_state():
    """
    Creates all session state keys with default empty values.
    Only sets a key if it does not already exist.
    This means calling it multiple times is safe — it won't overwrite existing data.
    """

    # The original uploaded dataframe — never modified after upload
    if "original_df" not in st.session_state:
        st.session_state.original_df = None

    # The working copy — all cleaning and transformations apply here
    if "working_df" not in st.session_state:
        st.session_state.working_df = None

    # The name of the uploaded file (e.g. "sales_data.csv")
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None

    # The file type detected on upload: "csv", "xlsx", or "json"
    if "uploaded_file_type" not in st.session_state:
        st.session_state.uploaded_file_type = None

    # A list of transformation steps applied so far
    # Each entry will be a dictionary with operation name, columns, parameters, timestamp
    if "transformation_log" not in st.session_state:
        st.session_state.transformation_log = []

    # A list of structured steps for JSON export (the reproducible recipe)
    if "recipe_steps" not in st.session_state:
        st.session_state.recipe_steps = []

    # A list or dataframe of rows that failed validation rules
    if "validation_violations" not in st.session_state:
        st.session_state.validation_violations = []

    if "validation_violations_df" not in st.session_state:
        st.session_state.validation_violations_df = None

    # A dictionary storing profiling results (shape, dtypes, missing counts, etc.)
    if "profile_summary" not in st.session_state:
        st.session_state.profile_summary = {}

    # A simple flag: True if a dataset has been successfully loaded, False otherwise
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    # Single-step undo — stores one previous copy of working_df
    if "undo_stack" not in st.session_state:
        st.session_state.undo_stack = None
    # Stores a short summary of the last transformation action
    if "last_action_summary" not in st.session_state:
        st.session_state.last_action_summary = None
    if "missing_snapshot" not in st.session_state:
        st.session_state.missing_snapshot = None
    if "outlier_snapshot" not in st.session_state:
        st.session_state.outlier_snapshot = None
    if "scaling_snapshot" not in st.session_state:
        st.session_state.scaling_snapshot = None


def data_is_loaded():
    """
    Returns True if a dataset is currently active in the session.
    Returns False if no dataset has been uploaded yet.
    Use this as a guard check before showing any data tools.
    """
    return st.session_state.get("data_loaded", False)


def reset_session_state():
    """
    Resets all session state values back to their empty defaults.
    This is called when the user clicks the Reset Session button.
    After this, the app behaves as if it was just opened for the first time.
    """
    st.session_state.original_df = None
    st.session_state.working_df = None
    st.session_state.uploaded_file_name = None
    st.session_state.uploaded_file_type = None
    st.session_state.transformation_log = []
    st.session_state.recipe_steps = []
    st.session_state.validation_violations = []
    st.session_state.profile_summary = {}
    st.session_state.data_loaded = False
    st.session_state.undo_stack = None
    st.session_state.last_action_summary = None
    
def render_sidebar_controls():
    """
    Renders shared sidebar control buttons on any page that calls this.
    Call this function near the top of any page that needs these controls.
    """
    from datetime import datetime

    if not data_is_loaded():
        return  # Don't show controls if no data is loaded
    # --- Last Action Summary ---
    summary = st.session_state.get("last_action_summary")
    if summary:
        st.sidebar.divider()
        st.sidebar.success(
            f"✅ **Last action:**\n\n"
            f"{summary['action']}\n\n"
            f"{summary['detail']}"
        )
    st.sidebar.divider()

    # Reset to original data
    if st.sidebar.button("🔄 Reset to Original Data", key="btn_reset_to_original"):
        st.session_state.working_df = st.session_state.original_df.copy()
        st.session_state.undo_stack = None
        st.session_state.transformation_log.append({
            "operation": "reset_to_original",
            "columns": [],
            "parameters": {"note": "Working data reset to original uploaded dataset"},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        st.rerun()

    # Undo last action
    if st.session_state.get("undo_stack") is not None:
        if st.sidebar.button("↩ Undo Last Action", key="btn_undo"):
            st.session_state.working_df = st.session_state.undo_stack.copy()
            st.session_state.undo_stack = None
            st.session_state.transformation_log.append({
                "operation": "undo_last_action",
                "columns": [],
                "parameters": {},
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
    else:
        st.sidebar.button("↩ Undo Last Action", disabled=True, key="btn_undo")

    # --- Reset Session --- always visible on every page
    if st.sidebar.button("🗑 Reset Session", key="btn_reset_session"):
        reset_session_state()
        st.rerun()

    st.sidebar.divider()
        
def set_last_action_summary(action, detail):
    """
    Stores a short readable summary of the last transformation for display.
    """
    st.session_state.last_action_summary = {
        "action": action,
        "detail": detail
    }