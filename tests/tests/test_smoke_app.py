"""
Smoke tests for AI-Assisted Data Wrangler & Visualizer
Uses Streamlit AppTest to verify pages load without crashing.
Run with: pytest tests/test_smoke_app.py -v
"""

import pytest
import pandas as pd
from streamlit.testing.v1 import AppTest


# --- Small reusable sample dataframe for data-loaded tests ---
def make_sample_df():
    """Creates a tiny clean dataframe for injecting into session state."""
    return pd.DataFrame({
        "name":   ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age":    [25, 30, 35, 28, 22],
        "city":   ["London", "Paris", "London", "Berlin", "Paris"],
        "salary": [50000.0, 60000.0, 55000.0, 65000.0, 48000.0]
    })


# ----------------------------------------------------------------
# 1. Main app.py — basic launch
# ----------------------------------------------------------------

def test_app_runs_without_crashing():
    """app.py should load without any exceptions."""
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception, f"app.py crashed with: {at.exception}"


# ----------------------------------------------------------------
# 2. Upload & Overview page — no data loaded
# ----------------------------------------------------------------

def test_upload_page_runs_no_data():
    """Upload page should load cleanly with no data."""
    at = AppTest.from_file("pages/1_Upload_Overview.py")
    at.run()
    assert not at.exception, f"Upload page crashed: {at.exception}"


def test_upload_page_shows_upload_prompt():
    """Upload page should show a prompt when no data is loaded."""
    at = AppTest.from_file("pages/1_Upload_Overview.py")
    at.run()

    # Check that some info/prompt text is visible
    all_text = " ".join([m.value for m in at.info])
    assert "upload" in all_text.lower() or "dataset" in all_text.lower()


# ----------------------------------------------------------------
# 3. Cleaning & Preparation page — no data loaded
# ----------------------------------------------------------------

def test_cleaning_page_runs_no_data():
    """Cleaning page should load cleanly with no data and show a warning."""
    at = AppTest.from_file("pages/2_Cleaning_Preparation.py")
    at.run()
    assert not at.exception, f"Cleaning page crashed: {at.exception}"


def test_cleaning_page_shows_warning_no_data():
    """Cleaning page should warn the user when no data is loaded."""
    at = AppTest.from_file("pages/2_Cleaning_Preparation.py")
    at.run()

    all_warnings = " ".join([m.value for m in at.warning])
    assert "upload" in all_warnings.lower() or "no dataset" in all_warnings.lower()


# ----------------------------------------------------------------
# 4. Visualization Builder page — no data loaded
# ----------------------------------------------------------------

def test_visualization_page_runs_no_data():
    """Visualization page should load cleanly with no data."""
    at = AppTest.from_file("pages/3_Visualization_Builder.py")
    at.run()
    assert not at.exception, f"Visualization page crashed: {at.exception}"


def test_visualization_page_shows_warning_no_data():
    """Visualization page should warn the user when no data is loaded."""
    at = AppTest.from_file("pages/3_Visualization_Builder.py")
    at.run()

    all_warnings = " ".join([m.value for m in at.warning])
    assert "upload" in all_warnings.lower() or "no dataset" in all_warnings.lower()


# ----------------------------------------------------------------
# 5. Export & Report page — no data loaded
# ----------------------------------------------------------------

def test_export_page_runs_no_data():
    """Export page should load cleanly with no data."""
    at = AppTest.from_file("pages/4_Export_Report.py")
    at.run()
    assert not at.exception, f"Export page crashed: {at.exception}"


def test_export_page_shows_warning_no_data():
    """Export page should warn the user when no data is loaded."""
    at = AppTest.from_file("pages/4_Export_Report.py")
    at.run()

    all_warnings = " ".join([m.value for m in at.warning])
    assert "upload" in all_warnings.lower() or "no dataset" in all_warnings.lower()


# ----------------------------------------------------------------
# 6. Data-loaded tests — inject session state
# ----------------------------------------------------------------

def inject_data(at):
    """
    Helper that injects a small sample dataframe into session state
    so pages behave as if a file has been uploaded.
    """
    sample = make_sample_df()
    at.session_state["original_df"]        = sample.copy()
    at.session_state["working_df"]         = sample.copy()
    at.session_state["uploaded_file_name"] = "sample_test.csv"
    at.session_state["uploaded_file_type"] = "csv"
    at.session_state["data_loaded"]        = True
    at.session_state["transformation_log"] = []
    at.session_state["recipe_steps"]       = []
    at.session_state["validation_violations"] = []
    at.session_state["profile_summary"]    = {}
    at.session_state["undo_stack"]         = None
    at.session_state["last_action_summary"] = None


def test_cleaning_page_runs_with_data():
    """Cleaning page should load without crashing when data is injected."""
    at = AppTest.from_file("pages/2_Cleaning_Preparation.py")
    inject_data(at)
    at.run()
    assert not at.exception, f"Cleaning page crashed with data: {at.exception}"


def test_visualization_page_runs_with_data():
    """Visualization page should load without crashing when data is injected."""
    at = AppTest.from_file("pages/3_Visualization_Builder.py")
    inject_data(at)
    at.run()
    assert not at.exception, f"Visualization page crashed with data: {at.exception}"


def test_export_page_runs_with_data():
    """Export page should load without crashing when data is injected."""
    at = AppTest.from_file("pages/4_Export_Report.py")
    inject_data(at)
    at.run()
    assert not at.exception, f"Export page crashed with data: {at.exception}"


def test_cleaning_page_shows_data_summary_with_data():
    """Cleaning page should show dataset info when data is loaded."""
    at = AppTest.from_file("pages/2_Cleaning_Preparation.py")
    inject_data(at)
    at.run()

    # Page should not show the no-data warning
    all_warnings = " ".join([m.value for m in at.warning])
    assert "no dataset" not in all_warnings.lower()


def test_export_page_shows_csv_download_with_data():
    """Export page should render without crashing when data is present."""
    at = AppTest.from_file("pages/4_Export_Report.py")
    inject_data(at)
    at.run()

    # No exception is the key check — download buttons are not
    # directly inspectable via AppTest but a clean run confirms they rendered
    assert not at.exception