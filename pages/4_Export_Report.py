import pandas as pd
import streamlit as st
import io
from datetime import datetime

from utils.session_state import initialize_session_state, data_is_loaded, render_sidebar_controls
from utils.export_helpers import build_report_text   # <-- add this new line
# Always initialize session state at the top of every page
initialize_session_state()
render_sidebar_controls()

# --- Page Title and Description ---
st.title("Export & Report")

st.write(
    "Export your cleaned dataset, download a transformation report, "
    "and save a JSON recipe of your full cleaning workflow."
)

st.divider()

# --- Data Loaded Check ---
if not data_is_loaded():
    st.warning(
        "No dataset loaded yet. "
        "Please go to the **Upload & Overview** page first and upload a file."
    )
    st.stop()

# --- Everything below only runs when data is loaded ---

df = st.session_state.working_df

# ---- Dataset Info ----
st.subheader("Current Dataset Info")

col1, col2, col3 = st.columns(3)
col1.metric("File", st.session_state.uploaded_file_name)
col2.metric("Rows", df.shape[0])
col3.metric("Columns", df.shape[1])

st.divider()

# ---- Data Preview ----
st.subheader("Cleaned Data Preview (Top 10 Rows)")
st.dataframe(df.head(10), use_container_width=True)

st.divider()

# ---- Transformation Log Summary ----
st.subheader("Transformation Log Summary")

log = st.session_state.transformation_log

if not log:
    st.info("No transformations recorded yet.")
else:
    st.success(f"**{len(log)}** transformation(s) recorded.")

    for i, entry in enumerate(log, start=1):
        with st.expander(f"Step {i} — {entry['operation']}  ({entry['timestamp']})"):
            st.write(f"**Operation:** `{entry['operation']}`")
            st.write(f"**Timestamp:** {entry['timestamp']}")

            if entry["columns"]:
                st.write(f"**Columns affected:** {', '.join(entry['columns'])}")
            else:
                st.write("**Columns affected:** all columns")

            if entry["parameters"]:
                st.write("**Parameters:**")
                for key, value in entry["parameters"].items():
                    st.write(f"- {key}: `{value}`")

st.divider()

# ---- Export Data Section ----
st.subheader("Export Data")

st.write(
    "Download your cleaned dataset in your preferred format. "
    "All exports reflect the current state of the working dataset."
)

# Build a sensible filename based on the original uploaded file name
original_name = st.session_state.uploaded_file_name or "data"
# Strip the original extension and add _cleaned.csv
base_name = original_name.rsplit(".", 1)[0]
csv_filename = f"{base_name}_cleaned.csv"

# Convert working_df to CSV in memory — index=False keeps row numbers out
csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇ Download Cleaned Data as CSV",
    data=csv_data,
    file_name=csv_filename,
    mime="text/csv",
    key="download_csv"
)

st.divider()

# --- Excel Export ---
# Build a sensible filename based on the original uploaded file name
xlsx_filename = f"{base_name}_cleaned.xlsx"

# Write dataframe to an in-memory Excel file using openpyxl engine
xlsx_buffer = io.BytesIO()
with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Cleaned Data")

# Move buffer position back to the start before reading
xlsx_buffer.seek(0)

st.download_button(
    label="⬇ Download Cleaned Data as Excel",
    data=xlsx_buffer,
    file_name=xlsx_filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download_xlsx"
)

st.divider()

# --- JSON Export ---
json_filename = f"{base_name}_cleaned.json"

# orient="records" gives a clean list of row objects — easiest to read and reuse
json_data = df.to_json(orient="records", indent=2).encode("utf-8")

st.download_button(
    label="⬇ Download Cleaned Data as JSON",
    data=json_data,
    file_name=json_filename,
    mime="application/json",
    key="download_json"
)

st.divider()

# ---- JSON Recipe Export ----
st.subheader("Workflow Recipe Export")

st.write(
    "Download your full transformation workflow as a JSON file. "
    "This captures every cleaning step so the process can be reviewed or reproduced later."
)

import json

recipe = {
    "app": "AI-Assisted Data Wrangler & Visualizer",
    "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "source_file": st.session_state.get("uploaded_file_name") or "Unknown",
    "total_steps": len(log),
    "transformations": [
        {
            "operation": entry.get("operation", "unknown"),
            "timestamp": entry.get("timestamp", ""),
            "columns": entry.get("columns") or [],
            "parameters": entry.get("parameters") or {}
        }
        for entry in log
    ]
}

recipe_json = json.dumps(recipe, indent=2, default=str).encode("utf-8")
recipe_filename = f"{base_name}_workflow_recipe.json"

st.download_button(
    label="⬇ Download Workflow Recipe (.json)",
    data=recipe_json,
    file_name=recipe_filename,
    mime="application/json",
    key="download_recipe_json"
)

st.divider()

# ---- Transformation Report Section ----
st.subheader("Transformation Report")

st.write(
    "Download a full summary of every cleaning step applied in this session, "
    "or preview the report directly on this page."
)

# Build report text once using the shared helper.
# Make sure the final value is always a valid downloadable text payload.
file_name = st.session_state.get("uploaded_file_name", None)

try:
    raw_report = build_report_text(log, file_name)
except Exception as e:
    raw_report = (
        "Transformation Report\n"
        "=====================\n\n"
        f"Could not build the full report.\n"
        f"Error: {e}\n"
    )

# Normalize report into plain text
if raw_report is None:
    report_text = (
        "Transformation Report\n"
        "=====================\n\n"
        "No report content available.\n"
    )
elif isinstance(raw_report, bytes):
    report_text = raw_report.decode("utf-8", errors="replace")
elif isinstance(raw_report, str):
    report_text = raw_report
else:
    report_text = str(raw_report)

# Convert to bytes for safe download
report_bytes = report_text.encode("utf-8")

st.download_button(
    label="⬇ Download Transformation Report (.txt)",
    data=report_bytes,
    file_name="transformation_report.txt",
    mime="text/plain",
    key="download_report_txt"
)
st.divider()

# --- Current Export Summary ---
if data_is_loaded():
    df_summary = st.session_state.working_df

    with st.container():
        st.markdown("### 📦 Export Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("File", st.session_state.uploaded_file_name or "Unknown")
        col2.metric("Rows", df_summary.shape[0])
        col3.metric("Columns", df_summary.shape[1])
        col4.metric("Transformations", len(st.session_state.transformation_log))

        st.info(
            "**Available export formats:** "
            "CSV · Excel (.xlsx) · JSON · Transformation Report (.txt)"
        )

    st.divider()
# --- Reset Export View ---
if st.button("🔄 Reset Export View", key="btn_reset_export_view"):
    # Clear any export page specific session state keys
    # Currently minimal — structured for future export options/filters
    export_keys = [
        "export_row_count",
        "export_format_choice",
        "export_preview_rows"
    ]
    for key in export_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

# --- On-Page Report Preview ---
st.write("**Report Preview:**")

# Uses the same report_text string built above — preview matches download exactly
st.code(report_text, language=None)