import streamlit as st
import pandas as pd

from utils.session_state import initialize_session_state, data_is_loaded, render_sidebar_controls, set_last_action_summary
from utils.profiling import get_missing_values_summary
from utils.transformations import (
    fill_missing_with_constant,
    drop_rows_with_missing,
    remove_full_row_duplicates,
    remove_duplicates_by_columns,
    convert_column_types,
    standardize_text_case,
    replace_values_in_columns,
    group_rare_categories,
    analyze_outliers_iqr,
    remove_outliers_iqr,
    min_max_scale_columns,
    z_score_scale_columns,
    rename_column,
    drop_columns,
    create_calculated_column,
    merge_columns,
    split_column,
    build_log_entry
)
def set_last_action_summary(action, detail):
    """
    Stores a short readable summary of the last transformation action.
    Call this after every successful data-changing action.
    """
    st.session_state.last_action_summary = {
        "action": action,
        "detail": detail
    }

# Always initialize session state at the top of every page
initialize_session_state()
render_sidebar_controls()

# --- Page Title and Description ---
st.title("Cleaning & Preparation Studio")

st.write(
    "This is your data cleaning workspace. "
    "Here you will be able to handle missing values, remove duplicates, "
    "convert data types, clean categorical and numeric columns, "
    "apply scaling, and manage column operations. "
    "Every action will be recorded in a transformation log."
)

# --- Page Navigation ---
st.markdown(
    """
    <div style="background-color:#f0f2f6; padding:12px 16px; border-radius:8px; margin-bottom:8px;">
    <b>Jump to section:</b>&nbsp;&nbsp;
    <a href="#missing-values" style="margin-right:12px;">Missing Values</a>
    <a href="#duplicates" style="margin-right:12px;">Duplicates</a>
    <a href="#data-types" style="margin-right:12px;">Data Types</a>
    <a href="#text-cleaning" style="margin-right:12px;">Text Cleaning</a>
    <a href="#category-tools" style="margin-right:12px;">Category Tools</a>
    <a href="#outliers" style="margin-right:12px;">Outliers</a>
    <a href="#scaling" style="margin-right:12px;">Scaling</a>
    <a href="#column-operations" style="margin-right:12px;">Column Operations</a>
    <a href="#validation" style="margin-right:12px;">Validation</a>
    <a href="#log">Transformation Log</a>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Current Data Summary ---
if data_is_loaded():
    _df = st.session_state.working_df
    _numeric = _df.select_dtypes(include=["number"]).shape[1]
    _categorical = _df.select_dtypes(include=["object", "category"]).shape[1]

    with st.container():
        st.markdown("### 🧹 Current Data Summary")

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("File", st.session_state.uploaded_file_name or "Unknown")
        col2.metric("Rows", _df.shape[0])
        col3.metric("Columns", _df.shape[1])
        col4.metric("Numeric", _numeric)
        col5.metric("Categorical", _categorical)
        col6.metric("Transformations", len(st.session_state.transformation_log))

    st.divider()

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

# Show current dataset shape
rows, columns = df.shape
st.caption(f"Working dataset: **{rows} rows × {columns} columns**")

st.divider()

# ---- Section 1: Missing Values Analysis ----
st.markdown('<a name="missing-values"></a>', unsafe_allow_html=True)
st.subheader("Missing Values Analysis")

st.write(
    "The table below shows which columns have missing values, "
    "how many are missing, and what percentage of the column is affected."
)

missing_summary = get_missing_values_summary(df)

if missing_summary.empty:
    st.success("Great — no missing values found in the current dataset.")
else:
    st.warning(
        f"Missing values detected in **{len(missing_summary)}** column(s). "
        "See details below."
    )
    st.dataframe(missing_summary, use_container_width=True)

st.divider()

# ---- Section 1b: Before / After Missing Values Preview ----
st.subheader("Before / After Missing Values Preview")

st.write(
    "Take a snapshot of the current missing value counts before applying "
    "a cleaning action. After the action runs the comparison will appear "
    "automatically so you can see exactly what changed."
)

col_snap1, col_snap2 = st.columns(2)

with col_snap1:
    if st.button("📸 Take Snapshot", key="btn_take_missing_snapshot"):
        # Store current missing counts per column as a simple dict
        st.session_state.missing_snapshot = df.isnull().sum().to_dict()
        st.success("✅ Snapshot taken — apply a missing-value action and return here to compare.")

with col_snap2:
    if st.button("🗑 Clear Snapshot", key="btn_clear_missing_snapshot"):
        st.session_state.missing_snapshot = None
        st.info("Snapshot cleared.")

# Show comparison if a snapshot exists
if st.session_state.get("missing_snapshot"):
    snapshot = st.session_state.missing_snapshot
    current_missing = df.isnull().sum().to_dict()

    # Build comparison only for columns that had or now have missing values
    comparison_rows = []
    all_cols_union = set(snapshot.keys()) | set(current_missing.keys())

    for col in all_cols_union:
        before = snapshot.get(col, 0)
        after = current_missing.get(col, 0)
        diff = before - after
        if before > 0 or after > 0:
            comparison_rows.append({
                "Column": col,
                "Missing Before": before,
                "Missing After": after,
                "Filled / Removed": diff
            })

    if not comparison_rows:
        st.info("No missing values detected in snapshot or current dataset.")
    else:
        import pandas as pd
        comparison_df = pd.DataFrame(comparison_rows)
        comparison_df.index = range(1, len(comparison_df) + 1)
        st.dataframe(comparison_df, use_container_width=True)

st.divider()

# ---- Section 2: Fill Missing Values with a Constant ----
st.subheader("Fill Missing Values with a Constant")

st.write(
    "Select one or more columns and provide a value to fill in wherever "
    "data is missing. For numeric columns, use a number (e.g. 0). "
    "For text columns, use a word (e.g. Unknown)."
)

columns_to_fill = st.multiselect(
    label="Select columns to fill",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="fill_constant_columns"
)

fill_value = st.text_input(
    label="Fill value",
    placeholder="e.g. 0 or Unknown",
    key="fill_constant_value"
)

if st.button("Apply — Fill with Constant", key="btn_fill_constant"):

    if not columns_to_fill:
        st.error("Please select at least one column.")

    elif fill_value.strip() == "":
        st.error("Please enter a fill value.")

    else:
        missing_before = df[columns_to_fill].isnull().sum().sum()

        if missing_before == 0:
            st.info("Nothing to change — no missing values found in the selected columns.")

        else:
            updated_df = fill_missing_with_constant(df, columns_to_fill, fill_value)
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="fill_missing_with_constant",
                columns=columns_to_fill,
                parameters={"fill_value": fill_value}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — filled **{missing_before}** missing value(s) across **{len(columns_to_fill)}** column(s) with `{fill_value}`.")
            set_last_action_summary("Fill Missing Values", f"Filled {missing_before} missing value(s) with '{fill_value}'")
            st.rerun()

st.divider()

# ---- Section 2b: Fill Missing Values with Mean / Median / Mode ----
st.subheader("Fill Missing Values with Mean / Median / Mode")

st.write(
    "Select a column and a statistical fill method. "
    "Mean and Median are only available for numeric columns. "
    "Mode works for any column type."
)

# Separate numeric and all columns for safe method filtering
numeric_cols_fill = df.select_dtypes(include=["number"]).columns.tolist()
all_cols_fill = df.columns.tolist()

fill_stat_column = st.selectbox(
    label="Select a column to fill",
    options=all_cols_fill,
    key="fill_stat_column"
)

# Determine which methods are valid for the selected column
is_numeric_col = fill_stat_column in numeric_cols_fill
available_methods = ["Mean", "Median", "Mode"] if is_numeric_col else ["Mode"]

if not is_numeric_col:
    st.info("Mean and Median are only available for numeric columns. Mode will be used.")

fill_stat_method = st.selectbox(
    label="Fill method",
    options=available_methods,
    key="fill_stat_method"
)

if st.button("Apply — Fill with Statistic", key="btn_fill_statistic"):

    missing_before = int(df[fill_stat_column].isnull().sum())

    if missing_before == 0:
        st.info(
            f"Nothing to change — no missing values found in `{fill_stat_column}`."
        )

    else:
        # Calculate the fill value based on chosen method
        fill_val = None
        method_used = fill_stat_method.lower()

        if fill_stat_method == "Mean":
            fill_val = df[fill_stat_column].mean()

        elif fill_stat_method == "Median":
            fill_val = df[fill_stat_column].median()

        elif fill_stat_method == "Mode":
            mode_result = df[fill_stat_column].mode()
            if mode_result.empty:
                st.warning(
                    f"⚠️ Could not compute mode for `{fill_stat_column}`. "
                    "The column may have no non-missing values."
                )
                st.stop()
            fill_val = mode_result.iloc[0]

        # Apply the fill
        updated_df = df.copy()
        updated_df[fill_stat_column] = updated_df[fill_stat_column].fillna(fill_val)
        missing_after = int(updated_df[fill_stat_column].isnull().sum())

        # Save undo state and update session
        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="fill_missing_with_statistic",
            columns=[fill_stat_column],
            parameters={
                "method": fill_stat_method,
                "fill_value": round(float(fill_val), 4) if isinstance(fill_val, float) else str(fill_val)
            }
        )
        st.session_state.transformation_log.append(log_entry)

        set_last_action_summary(
            "Fill Missing with Statistic",
            f"Filled `{fill_stat_column}` using {fill_stat_method}"
        )

        st.success(
            f"✅ Done — filled **{missing_before}** missing value(s) in "
            f"`{fill_stat_column}` using **{fill_stat_method}** "
            f"(`{round(float(fill_val), 4) if isinstance(fill_val, float) else fill_val}`). "
            f"Missing before: **{missing_before}** → after: **{missing_after}**."
        )
        st.rerun()

st.divider()

# ---- Section 2c: Fill Missing Values with Forward Fill / Backward Fill ----
st.subheader("Fill Missing Values with Forward Fill / Backward Fill")

st.write(
    "Forward Fill copies the last known value downward to fill gaps. "
    "Backward Fill copies the next known value upward. "
    "Useful for ordered data like time series."
)

ffill_column = st.selectbox(
    label="Select a column to fill",
    options=df.columns.tolist(),
    key="ffill_column"
)

ffill_method = st.selectbox(
    label="Fill method",
    options=["Forward Fill", "Backward Fill"],
    key="ffill_method"
)

if st.button("Apply — Forward / Backward Fill", key="btn_ffill"):

    missing_before = int(df[ffill_column].isnull().sum())

    if missing_before == 0:
        st.info(
            f"Nothing to change — no missing values found in `{ffill_column}`."
        )

    else:
        updated_df = df.copy()

        if ffill_method == "Forward Fill":
            updated_df[ffill_column] = updated_df[ffill_column].ffill()
        else:
            updated_df[ffill_column] = updated_df[ffill_column].bfill()

        missing_after = int(updated_df[ffill_column].isnull().sum())

        # Save undo state and update session
        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="fill_missing_forward_backward",
            columns=[ffill_column],
            parameters={"method": ffill_method}
        )
        st.session_state.transformation_log.append(log_entry)

        set_last_action_summary(
            "Forward / Backward Fill",
            f"Filled `{ffill_column}` using {ffill_method}"
        )

        st.success(
            f"✅ Done — applied **{ffill_method}** to `{ffill_column}`. "
            f"Missing before: **{missing_before}** → after: **{missing_after}**."
        )
        st.rerun()

st.divider()

# ---- Section 2d: Fill Missing Values with Most Frequent Category ----
st.subheader("Fill Missing Values with Most Frequent Category")

st.write(
    "Fills missing values in a selected column using the most frequently "
    "occurring non-missing value. Works for any column type but is most "
    "useful for categorical and text columns."
)

most_freq_column = st.selectbox(
    label="Select a column to fill",
    options=df.columns.tolist(),
    key="most_freq_column"
)

# Show the most frequent value as a helpful preview before the user clicks
most_freq_preview = df[most_freq_column].mode()
if not most_freq_preview.empty:
    st.caption(
        f"Most frequent value in `{most_freq_column}`: "
        f"**{most_freq_preview.iloc[0]}**"
    )

if st.button("Apply — Fill with Most Frequent", key="btn_fill_most_freq"):

    missing_before = int(df[most_freq_column].isnull().sum())

    if missing_before == 0:
        st.info(
            f"Nothing to change — no missing values found in `{most_freq_column}`."
        )

    else:
        # Compute the most frequent non-missing value
        mode_result = df[most_freq_column].mode()

        if mode_result.empty:
            st.warning(
                f"⚠️ Could not find a non-missing value to use in "
                f"`{most_freq_column}`. The column may be entirely empty."
            )

        else:
            fill_val = mode_result.iloc[0]

            updated_df = df.copy()
            updated_df[most_freq_column] = updated_df[most_freq_column].fillna(fill_val)
            missing_after = int(updated_df[most_freq_column].isnull().sum())

            # Save undo state and update session
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="fill_missing_most_frequent",
                columns=[most_freq_column],
                parameters={"fill_value": str(fill_val)}
            )
            st.session_state.transformation_log.append(log_entry)

            set_last_action_summary(
                "Fill with Most Frequent",
                f"Filled `{most_freq_column}` with most frequent value: `{fill_val}`"
            )

            st.success(
                f"✅ Done — filled `{most_freq_column}` with most frequent value "
                f"`{fill_val}`. "
                f"Missing before: **{missing_before}** → after: **{missing_after}**."
            )
            st.rerun()

st.divider()

# ---- Section 3: Drop Rows with Missing Values ----
st.subheader("Drop Rows with Missing Values")

st.write(
    "Select one or more columns. Any row that has a missing value in "
    "at least one of those columns will be removed from the dataset."
)

columns_to_drop = st.multiselect(
    label="Select columns to check for missing values",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="drop_missing_columns"
)

if st.button("Apply — Drop Rows", key="btn_drop_missing"):

    if not columns_to_drop:
        st.error("Please select at least one column.")

    else:
        rows_before = len(df)
        rows_after = len(df.dropna(subset=columns_to_drop))
        rows_removed = rows_before - rows_after

        if rows_removed == 0:
            st.info("Nothing to change — no rows with missing values found in the selected columns.")
        else:
            updated_df = drop_rows_with_missing(df, columns_to_drop)
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="drop_rows_with_missing",
                columns=columns_to_drop,
                parameters={"rows_removed": rows_removed}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(
                f"Removed **{rows_removed}** row(s). "
                f"Dataset now has **{len(updated_df)} rows × {updated_df.shape[1]} columns**."
            )
            set_last_action_summary("Drop Rows", f"Removed {rows_removed} row(s) with missing values")
            st.rerun()

st.divider()

# ---- Section 3b: Drop Columns Above Missing Threshold ----
st.subheader("Drop Columns Above Missing Threshold (%)")

st.write(
    "Set a missing-value percentage threshold. "
    "Any column where more than that percentage of values are missing "
    "will be automatically dropped from the dataset."
)

missing_threshold = st.slider(
    label="Maximum allowed missing percentage (%)",
    min_value=1,
    max_value=100,
    value=50,
    step=1,
    key="missing_threshold_pct"
)

# Show a compact preview of which columns would be affected
missing_pct_series = (df.isnull().sum() / len(df) * 100).round(2)
cols_to_drop_thresh = missing_pct_series[missing_pct_series > missing_threshold].index.tolist()

if cols_to_drop_thresh:
    st.warning(
        f"**{len(cols_to_drop_thresh)}** column(s) exceed {missing_threshold}% missing: "
        f"{', '.join(cols_to_drop_thresh)}"
    )
else:
    st.info(f"No columns exceed {missing_threshold}% missing with the current threshold.")

if st.button("Apply — Drop Columns by Missing Threshold", key="btn_drop_cols_threshold"):

    if not cols_to_drop_thresh:
        st.info(
            f"Nothing to change — no columns exceed {missing_threshold}% missing values."
        )

    else:
        cols_before = df.shape[1]
        updated_df = df.drop(columns=cols_to_drop_thresh)
        cols_after = updated_df.shape[1]

        # Save undo state before modifying
        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="drop_columns_above_missing_threshold",
            columns=cols_to_drop_thresh,
            parameters={
                "threshold_pct": missing_threshold,
                "columns_dropped": len(cols_to_drop_thresh)
            }
        )
        st.session_state.transformation_log.append(log_entry)

        set_last_action_summary(
            "Drop Columns by Missing Threshold",
            f"Dropped {len(cols_to_drop_thresh)} column(s) above {missing_threshold}% missing"
        )

        st.success(
            f"✅ Done — dropped **{len(cols_to_drop_thresh)}** column(s): "
            f"{', '.join(cols_to_drop_thresh)}. "
            f"Columns before: **{cols_before}** → after: **{cols_after}**."
        )
        st.rerun()

st.divider()

# ---- Section 4: Duplicate Rows Analysis ----
st.markdown('<a name="duplicates"></a>', unsafe_allow_html=True)
st.subheader("Duplicate Rows Analysis")

st.write(
    "A duplicate row is one where every column value is identical to another row. "
    "The preview below shows all rows involved in a duplication — "
    "both the original and its copy."
)

duplicate_count = int(df.duplicated().sum())

if duplicate_count == 0:
    st.success("No duplicate rows found in the current dataset.")
else:
    st.warning(
        f"Found **{duplicate_count}** duplicate row(s) in the current dataset."
    )
    duplicate_rows = df[df.duplicated(keep=False)]
    st.write(
        f"Showing all **{len(duplicate_rows)}** rows involved in duplications "
        f"(includes both originals and their copies):"
    )
    st.dataframe(duplicate_rows, use_container_width=True)

st.divider()

# ---- Section 5: Remove Full-Row Duplicates ----
st.subheader("Remove Full-Row Duplicates")

st.write(
    "Remove rows that are exact copies of another row. "
    "Choose whether to keep the first or last occurrence of each duplicated row."
)

keep_option_full = st.selectbox(
    label="Which occurrence to keep?",
    options=["first", "last"],
    key="dedup_keep_option_full"
)

if st.button("Apply — Remove Full-Row Duplicates", key="btn_remove_duplicates_full"):

    current_duplicate_count = int(df.duplicated().sum())

    if current_duplicate_count == 0:
        st.info("Nothing to change — no duplicate rows found in the current dataset.")

    else:
        rows_before = len(df)
        updated_df = remove_full_row_duplicates(df, keep=keep_option_full)
        rows_removed = rows_before - len(updated_df)

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="remove_full_row_duplicates",
            columns=[],
            parameters={"keep": keep_option_full, "rows_removed": rows_removed}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — removed **{rows_removed}** duplicate row(s). Dataset now has **{len(updated_df)} rows × {updated_df.shape[1]} columns**.")
        set_last_action_summary("Remove Duplicates", f"Removed {rows_removed} duplicate row(s)")
        st.rerun()

st.divider()

# ---- Section 6: Remove Duplicates by Selected Columns ----
st.subheader("Remove Duplicates by Selected Columns")

st.write(
    "Choose specific columns to define what counts as a duplicate. "
    "Two rows are treated as duplicates if they match on the selected columns — "
    "even if other columns differ."
)

columns_for_dedup = st.multiselect(
    label="Select columns to check for duplicates",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="dedup_by_columns_select"
)

keep_option_cols = st.selectbox(
    label="Which occurrence to keep?",
    options=["first", "last"],
    key="dedup_keep_option_cols"
)

if st.button("Apply — Remove Duplicates by Columns", key="btn_remove_duplicates_cols"):

    if not columns_for_dedup:
        st.error("Please select at least one column.")

    else:
        rows_before = len(df)
        rows_after_preview = len(df.drop_duplicates(subset=columns_for_dedup))
        rows_to_remove = rows_before - rows_after_preview

        if rows_to_remove == 0:
            st.info("Nothing to change — no duplicates found based on the selected columns.")
        else:
            updated_df = remove_duplicates_by_columns(
                df,
                columns=columns_for_dedup,
                keep=keep_option_cols
            )
            rows_removed = rows_before - len(updated_df)

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="remove_duplicates_by_columns",
                columns=columns_for_dedup,
                parameters={"keep": keep_option_cols, "rows_removed": rows_removed}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — removed **{rows_removed}** row(s) based on selected columns. Dataset now has **{len(updated_df)} rows × {updated_df.shape[1]} columns**.")
            set_last_action_summary("Remove Duplicates by Columns", f"Removed {rows_removed} row(s) based on {', '.join(columns_for_dedup)}")
            st.rerun()

st.divider()

# ---- Section 7: Data Type Overview & Conversion ----
st.markdown('<a name="data-types"></a>', unsafe_allow_html=True)
st.subheader("Data Type Overview & Conversion")

st.write(
    "The table below shows the current data type of each column. "
    "Use the controls below to convert selected columns to a different type."
)

dtype_overview = pd.DataFrame({
    "Column Name": df.columns,
    "Current Data Type": df.dtypes.values
})
dtype_overview.index = range(1, len(dtype_overview) + 1)
st.dataframe(dtype_overview, use_container_width=True)

columns_to_convert = st.multiselect(
    label="Select columns to convert",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="convert_type_columns"
)

target_type = st.selectbox(
    label="Convert to type",
    options=["string", "category", "numeric", "datetime"],
    help=(
        "string   — plain text. "
        "category — efficient type for columns with few unique values. "
        "numeric  — number (non-convertible values become NaN). "
        "datetime — date/time (non-convertible values become NaT)."
    ),
    key="convert_target_type"
)

# --- Extra controls shown only when datetime is selected ---
datetime_parse_mode = None
datetime_custom_format = None

if target_type == "datetime":
    st.write("**Datetime Parse Options**")
    datetime_parse_mode = st.selectbox(
        label="Parse mode",
        options=["Auto Parse", "Custom Format"],
        help=(
            "Auto Parse — pandas will try to detect the format automatically. "
            "Custom Format — you specify the exact format string (e.g. %d/%m/%Y)."
        ),
        key="datetime_parse_mode"
    )

    if datetime_parse_mode == "Custom Format":
        datetime_custom_format = st.text_input(
            label="Datetime format string",
            placeholder="e.g. %d/%m/%Y or %Y-%m-%d %H:%M:%S",
            key="datetime_custom_format"
        )
        st.caption(
            "Common formats: `%d/%m/%Y` · `%Y-%m-%d` · `%m-%d-%Y` · "
            "`%Y-%m-%d %H:%M:%S`"
        )

if st.button("Apply — Convert Types", key="btn_convert_types"):

    if not columns_to_convert:
        st.error("Please select at least one column.")

    elif target_type == "datetime" and datetime_parse_mode == "Custom Format" and not datetime_custom_format:
        st.error("Please enter a datetime format string or switch to Auto Parse.")

    else:
        updated_df = df.copy()

        # Handle datetime separately for richer parsing control
        if target_type == "datetime":
            for col in columns_to_convert:
                non_null_before = int(updated_df[col].notna().sum())

                if datetime_parse_mode == "Custom Format" and datetime_custom_format:
                    updated_df[col] = pd.to_datetime(
                        updated_df[col],
                        format=datetime_custom_format.strip(),
                        errors="coerce"
                    )
                else:
                    # Auto parse — let pandas infer the format safely
                    updated_df[col] = pd.to_datetime(
                        updated_df[col],
                        infer_datetime_format=True,
                        errors="coerce"
                    )

                successfully_parsed = int(updated_df[col].notna().sum())
                failed_count = non_null_before - successfully_parsed

            # Build log parameters
            dt_params = {
                "target_type": "datetime",
                "parse_mode": datetime_parse_mode or "Auto Parse"
            }
            if datetime_parse_mode == "Custom Format" and datetime_custom_format:
                dt_params["custom_format"] = datetime_custom_format.strip()
            dt_params["columns"] = columns_to_convert

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="convert_to_datetime",
                columns=columns_to_convert,
                parameters=dt_params
            )
            st.session_state.transformation_log.append(log_entry)

            set_last_action_summary(
                "Convert to Datetime",
                f"Parsed {len(columns_to_convert)} column(s) — "
                f"mode: {datetime_parse_mode or 'Auto Parse'}"
            )

            # Show compact before/after for the last processed column
            st.success(
                f"✅ Done — converted **{len(columns_to_convert)}** column(s) to datetime "
                f"using **{datetime_parse_mode or 'Auto Parse'}**. "
                f"Successfully parsed: **{successfully_parsed}** · "
                f"Failed (NaT): **{failed_count}**."
            )

        else:
            # All other types — use existing helper
            updated_df = convert_column_types(df, columns_to_convert, target_type)

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="convert_column_types",
                columns=columns_to_convert,
                parameters={"target_type": target_type}
            )
            st.session_state.transformation_log.append(log_entry)

            set_last_action_summary(
                "Convert Types",
                f"Converted {len(columns_to_convert)} column(s) to `{target_type}`"
            )

            st.success(
                f"✅ Done — converted **{len(columns_to_convert)}** column(s) to "
                f"`{target_type}`."
            )

        st.rerun()

st.divider()

# ---- Section 7b: Dirty Numeric String Cleaning ----
st.subheader("Dirty Numeric String Cleaning")

st.write(
    "Select a column that contains numbers stored as messy text — "
    "for example values like `$1,200.50`, `€ 900`, or `75%`. "
    "This tool strips common noise characters and converts the result to numeric. "
    "Values that still cannot be converted will become NaN safely."
)

# Show only object/string columns since numeric columns don't need this
dirty_numeric_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

if not dirty_numeric_cols:
    st.info("No text or category columns found in the current dataset.")

else:
    dirty_col = st.selectbox(
        label="Select a column to clean and convert",
        options=dirty_numeric_cols,
        key="dirty_numeric_column"
    )

    st.write("**Characters to strip before conversion:**")

    strip_col1, strip_col2, strip_col3 = st.columns(3)

    with strip_col1:
        strip_commas   = st.checkbox("Commas  `,`",          value=True, key="strip_commas")
        strip_spaces   = st.checkbox("Spaces  ` `",          value=True, key="strip_spaces")

    with strip_col2:
        strip_dollar   = st.checkbox("Dollar  `$`",          value=True, key="strip_dollar")
        strip_euro     = st.checkbox("Euro  `€`",            value=True, key="strip_euro")

    with strip_col3:
        strip_pound    = st.checkbox("Pound  `£`",           value=True, key="strip_pound")
        strip_percent  = st.checkbox("Percent  `%`",         value=True, key="strip_percent")

    # Show a small preview of raw values before cleaning
    st.caption("Sample raw values from selected column:")
    st.write(df[dirty_col].dropna().head(5).tolist())

    if st.button("Apply — Clean and Convert to Numeric", key="btn_dirty_numeric"):

        non_null_before = int(df[dirty_col].notna().sum())

        if non_null_before == 0:
            st.info(f"Nothing to change — `{dirty_col}` has no non-missing values.")

        else:
            updated_df = df.copy()

            # Build the set of characters to strip based on user selections
            chars_to_strip = ""
            stripped_chars = []

            if strip_commas:
                chars_to_strip += ","
                stripped_chars.append("commas")
            if strip_spaces:
                chars_to_strip += " "
                stripped_chars.append("spaces")
            if strip_dollar:
                chars_to_strip += "$"
                stripped_chars.append("$")
            if strip_euro:
                chars_to_strip += "€"
                stripped_chars.append("€")
            if strip_pound:
                chars_to_strip += "£"
                stripped_chars.append("£")
            if strip_percent:
                chars_to_strip += "%"
                stripped_chars.append("%")

            # Apply character stripping using str.replace for each character
            cleaned_series = updated_df[dirty_col].astype(str)

            for char in chars_to_strip:
                cleaned_series = cleaned_series.str.replace(char, "", regex=False)

            # Strip any remaining outer whitespace after removal
            cleaned_series = cleaned_series.str.strip()

            # Replace empty strings with NaN before numeric conversion
            cleaned_series = cleaned_series.replace("", float("nan"))

            # Convert to numeric safely — failures become NaN
            updated_df[dirty_col] = pd.to_numeric(cleaned_series, errors="coerce")

            successfully_converted = int(updated_df[dirty_col].notna().sum())
            failed_count = non_null_before - successfully_converted

            # Save undo state and update session
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="dirty_numeric_string_cleaning",
                columns=[dirty_col],
                parameters={
                    "stripped_characters": stripped_chars,
                    "converted_to": "numeric"
                }
            )
            st.session_state.transformation_log.append(log_entry)

            set_last_action_summary(
                "Dirty Numeric Cleaning",
                f"Cleaned and converted `{dirty_col}` to numeric"
            )

            st.success(
                f"✅ Done — cleaned `{dirty_col}` and converted to numeric. "
                f"Non-null before: **{non_null_before}** · "
                f"Successfully converted: **{successfully_converted}** · "
                f"Failed (NaN): **{failed_count}**."
            )
            st.rerun()

st.divider()

# ---- Section 8: Standardize Text Case ---- NEW
st.markdown('<a name="text-cleaning"></a>', unsafe_allow_html=True)
st.subheader("Standardize Text Case")

st.write(
    "Convert text in selected columns to a consistent case. "
    "This helps avoid mismatches where the same value is stored differently — "
    "for example 'London', 'london', and 'LONDON' would all be treated as different "
    "values without standardization."
)

# Only offer text/object columns since case conversion does not apply to numbers
text_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

if not text_columns:
    st.info("No text or category columns found in the current dataset.")

else:
    columns_for_case = st.multiselect(
        label="Select columns to standardize",
        options=text_columns,
        placeholder="Choose one or more text columns...",
        key="case_columns"
    )

    case_method = st.selectbox(
        label="Choose case format",
        options=["lower", "title"],
        help=(
            "lower — converts all text to lowercase (e.g. 'London' → 'london'). "
            "title — capitalizes the first letter of each word (e.g. 'john smith' → 'John Smith')."
        ),
        key="case_method"
    )

    if st.button("Apply — Standardize Case", key="btn_standardize_case"):

        if not columns_for_case:
            st.error("Please select at least one column.")

        else:
            updated_df = standardize_text_case(df, columns_for_case, case_method)
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="standardize_text_case",
                columns=columns_for_case,
                parameters={"case_method": case_method}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — applied `{case_method}` case to **{len(columns_for_case)}** column(s).")
            set_last_action_summary("Standardize Case", f"Applied '{case_method}' to {len(columns_for_case)} column(s)")
            st.rerun()

st.divider()

# ---- Section 9: Replace Values in Selected Columns ----
st.subheader("Replace Values in Selected Columns")

st.write(
    "Search for a specific value in selected columns and replace it with a new one. "
    "This is useful for fixing typos, correcting category labels, or "
    "standardizing inconsistent entries like 'N/A', 'na', or 'unknown'."
)

columns_for_replace = st.multiselect(
    label="Select columns to apply replacement to",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="replace_columns"
)

old_value_input = st.text_input(
    label="Value to replace (old value)",
    placeholder="e.g. N/A or unknwon",
    key="replace_old_value"
)

new_value_input = st.text_input(
    label="Replace with (new value)",
    placeholder="e.g. Unknown",
    key="replace_new_value"
)

if st.button("Apply — Replace Values", key="btn_replace_values"):

    if not columns_for_replace:
        st.error("Please select at least one column.")

    elif old_value_input.strip() == "":
        st.error("Please enter the value you want to replace.")

    else:
        updated_df = replace_values_in_columns(
            df,
            columns=columns_for_replace,
            old_value=old_value_input,
            new_value=new_value_input
        )

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="replace_values_in_columns",
            columns=columns_for_replace,
            parameters={"old_value": old_value_input, "new_value": new_value_input}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — replaced `{old_value_input}` with `{new_value_input}` in **{len(columns_for_replace)}** column(s).")
        set_last_action_summary("Replace Values", f"Replaced '{old_value_input}' with '{new_value_input}'")
        st.rerun()

st.divider()

# ---- Section 9b: Mapping Dictionary UI Table Editor ----
st.subheader("Mapping Dictionary — Bulk Value Replacement")

st.write(
    "Enter multiple old → new value pairs in the table below. "
    "All non-empty mappings will be applied to the selected column at once. "
    "Useful for renaming several category labels in one step."
)

mapping_column = st.selectbox(
    label="Select a column to apply mappings to",
    options=df.columns.tolist(),
    key="mapping_dict_column"
)

# Show current unique values as a hint
unique_vals = df[mapping_column].dropna().unique().tolist()
st.caption(
    f"Current unique values in `{mapping_column}` "
    f"({min(len(unique_vals), 10)} shown): "
    f"{', '.join(str(v) for v in unique_vals[:10])}"
)

st.write("**Edit your value mapping below:**")

# Build a default editable table with 6 empty rows
default_mapping = pd.DataFrame({
    "old_value": [""] * 6,
    "new_value": [""] * 6
})

mapping_table = st.data_editor(
    default_mapping,
    use_container_width=True,
    num_rows="dynamic",     # allows user to add/remove rows
    key="mapping_dict_table"
)

if st.button("Apply — Bulk Mapping", key="btn_apply_mapping"):

    # Filter out rows where either field is empty
    valid_rows = mapping_table[
        (mapping_table["old_value"].astype(str).str.strip() != "") &
        (mapping_table["new_value"].astype(str).str.strip() != "")
    ]

    if valid_rows.empty:
        st.error("Please enter at least one complete old → new mapping pair.")

    else:
        # Build the mapping dictionary from valid rows
        mapping_dict = dict(
            zip(
                valid_rows["old_value"].astype(str).str.strip(),
                valid_rows["new_value"].astype(str).str.strip()
            )
        )

        updated_df = df.copy()

        # Count how many values will actually change before applying
        values_changed = int(
            updated_df[mapping_column].astype(str).isin(mapping_dict.keys()).sum()
        )

        # Apply the mapping — values not in the dict are left unchanged
        updated_df[mapping_column] = (
            updated_df[mapping_column].astype(str).replace(mapping_dict)
        )

        # Save undo state and update session
        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="mapping_dict_replacement",
            columns=[mapping_column],
            parameters={
                "mapping_pairs": len(mapping_dict),
                "values_changed": values_changed,
                "mapping": mapping_dict
            }
        )
        st.session_state.transformation_log.append(log_entry)

        set_last_action_summary(
            "Bulk Mapping Replacement",
            f"Applied {len(mapping_dict)} mapping(s) to `{mapping_column}` "
            f"— {values_changed} value(s) changed"
        )

        st.success(
            f"✅ Done — applied **{len(mapping_dict)}** mapping pair(s) to "
            f"`{mapping_column}`. "
            f"Values changed: **{values_changed}**."
        )
        st.rerun()

# ---- Section 10: Group Rare Categories ----
st.markdown('<a name="category-tools"></a>', unsafe_allow_html=True)
st.subheader("Group Rare Categories")

st.write(
    "Select a column and set a minimum frequency threshold. "
    "Any category value that appears fewer times than the threshold "
    "will be replaced with the label 'Other'. "
    "Missing values will not be affected."
)

# Only offer text and category columns — rare grouping applies to categories
cat_cols_for_grouping = df.select_dtypes(
    include=["object", "category"]
).columns.tolist()

if not cat_cols_for_grouping:
    st.info("No text or category columns found in the current dataset.")

else:
    column_for_grouping = st.selectbox(
        label="Select a column",
        options=cat_cols_for_grouping,
        key="rare_category_column"
    )

    # Show the current value counts so the user can choose a sensible threshold
    st.write("Current value counts for selected column:")
    st.dataframe(
        df[column_for_grouping].value_counts().reset_index().rename(
            columns={"index": "Value", column_for_grouping: "Count"}
        ),
        use_container_width=True
    )

    min_freq = st.number_input(
        label="Minimum frequency threshold",
        min_value=1,
        value=10,
        step=1,
        help="Values appearing fewer times than this number will become 'Other'.",
        key="rare_category_min_freq"
    )

    if st.button("Apply — Group Rare Categories", key="btn_group_rare"):

        updated_df = group_rare_categories(df, column_for_grouping, min_freq)

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="group_rare_categories",
            columns=[column_for_grouping],
            parameters={"min_frequency": min_freq}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — rare categories in `{column_for_grouping}` below **{min_freq}** occurrence(s) grouped into 'Other'.")
        set_last_action_summary("Group Rare Categories", f"Grouped rare values in '{column_for_grouping}' below {min_freq} occurrences")
        st.rerun()

# ---- Section 11: Outlier Analysis (IQR Method) ----
st.markdown('<a name="outliers"></a>', unsafe_allow_html=True)
st.subheader("Outlier Analysis (IQR Method)")

st.write(
    "Select a numeric column to check for outliers using the IQR method. "
    "Outliers are values that fall unusually far from the middle of the data — "
    "specifically below Q1 − 1.5×IQR or above Q3 + 1.5×IQR. "
    "This section is for analysis only. Removal and capping tools will follow."
)

# Only offer numeric columns for outlier analysis
numeric_cols_for_outliers = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_outliers:
    st.info("No numeric columns found in the current dataset.")

else:
    outlier_column = st.selectbox(
        label="Select a numeric column to analyze",
        options=numeric_cols_for_outliers,
        key="outlier_analysis_column"
    )

    if st.button("Analyze Outliers", key="btn_analyze_outliers"):

        summary, outlier_rows = analyze_outliers_iqr(df, outlier_column)

        # Show the IQR summary values in a clean two-column layout
        st.write("**IQR Summary:**")

        col1, col2, col3 = st.columns(3)
        col1.metric("Q1", summary["Q1"])
        col2.metric("Q3", summary["Q3"])
        col3.metric("IQR", summary["IQR"])

        col4, col5, col6 = st.columns(3)
        col4.metric("Lower Bound", summary["Lower Bound"])
        col5.metric("Upper Bound", summary["Upper Bound"])
        col6.metric("Outlier Count", summary["Outlier Count"])

        st.divider()

        if summary["Outlier Count"] == 0:
            st.success(
                f"No outliers detected in `{outlier_column}` "
                "using the IQR method."
            )
        else:
            st.warning(
                f"Found **{summary['Outlier Count']}** outlier row(s) "
                f"in `{outlier_column}`. Preview below:"
            )
            st.dataframe(outlier_rows, use_container_width=True)

st.divider()

# ---- Section 12b: Cap / Winsorize Outliers (IQR Method) ----
st.subheader("Cap / Winsorize Outliers (IQR Method)")

st.write(
    "Instead of removing outlier rows, this tool caps extreme values at the "
    "IQR bounds. Values below Q1 − 1.5×IQR are raised to the lower bound. "
    "Values above Q3 + 1.5×IQR are lowered to the upper bound. "
    "No rows are removed."
)

numeric_cols_for_cap = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_cap:
    st.info("No numeric columns found in the current dataset.")

else:
    cap_column = st.selectbox(
        label="Select a numeric column to cap",
        options=numeric_cols_for_cap,
        key="cap_outlier_column"
    )

    # Calculate and preview IQR bounds before user clicks
    col_data = df[cap_column].dropna()
    q1 = col_data.quantile(0.25)
    q3 = col_data.quantile(0.75)
    iqr = q3 - q1
    lower_bound = round(q1 - 1.5 * iqr, 4)
    upper_bound = round(q3 + 1.5 * iqr, 4)

    low_outlier_count  = int((df[cap_column] < lower_bound).sum())
    high_outlier_count = int((df[cap_column] > upper_bound).sum())

    # Show bounds preview so user knows what will be capped
    prev_col1, prev_col2, prev_col3, prev_col4 = st.columns(4)
    prev_col1.metric("Lower Bound", lower_bound)
    prev_col2.metric("Upper Bound", upper_bound)
    prev_col3.metric("Values Below Bound", low_outlier_count)
    prev_col4.metric("Values Above Bound", high_outlier_count)

    if st.button("Apply — Cap Outliers", key="btn_cap_outliers"):

        if low_outlier_count == 0 and high_outlier_count == 0:
            st.info(
                f"Nothing to change — no outliers found in "
                f"`{cap_column}` using the IQR method."
            )

        else:
            updated_df = df.copy()

            # Clip values to the IQR bounds — values outside are pulled to the bound
            updated_df[cap_column] = updated_df[cap_column].clip(
                lower=lower_bound,
                upper=upper_bound
            )

            # Save undo state and update session
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="cap_outliers_iqr",
                columns=[cap_column],
                parameters={
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "low_values_capped": low_outlier_count,
                    "high_values_capped": high_outlier_count
                }
            )
            st.session_state.transformation_log.append(log_entry)

            set_last_action_summary(
                "Cap / Winsorize Outliers",
                f"Capped `{cap_column}` — "
                f"{low_outlier_count} low, {high_outlier_count} high value(s) capped"
            )

            st.success(
                f"✅ Done — outliers in `{cap_column}` capped to IQR bounds. "
                f"Lower bound: **{lower_bound}** · Upper bound: **{upper_bound}** · "
                f"Low values capped: **{low_outlier_count}** · "
                f"High values capped: **{high_outlier_count}**."
            )
            st.rerun()

st.divider()

# ---- Section 11b: Outlier Impact Summary (Before / After) ----
st.subheader("Outlier Impact Summary (Before / After)")

st.write(
    "Take a snapshot of current outlier counts before applying a removal "
    "or capping action. The comparison will appear automatically "
    "so you can see exactly what changed."
)

# Column selector for the snapshot
numeric_cols_for_snapshot = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_snapshot:
    st.info("No numeric columns found in the current dataset.")

else:
    snapshot_col = st.selectbox(
        label="Select a numeric column to track",
        options=numeric_cols_for_snapshot,
        key="outlier_snapshot_column"
    )

    snap_col1, snap_col2 = st.columns(2)

    with snap_col1:
        if st.button("📸 Take Outlier Snapshot", key="btn_take_outlier_snapshot"):

            # Calculate IQR bounds and outlier count for selected column
            col_data = df[snapshot_col].dropna()
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1
            lb = round(q1 - 1.5 * iqr, 4)
            ub = round(q3 + 1.5 * iqr, 4)
            outlier_count = int(
                ((df[snapshot_col] < lb) | (df[snapshot_col] > ub)).sum()
            )

            st.session_state.outlier_snapshot = {
                "column":        snapshot_col,
                "row_count":     len(df),
                "outlier_count": outlier_count,
                "lower_bound":   lb,
                "upper_bound":   ub
            }
            st.success(
                f"✅ Snapshot taken for `{snapshot_col}` — "
                f"{outlier_count} outlier(s) detected."
            )

    with snap_col2:
        if st.button("🗑 Clear Outlier Snapshot", key="btn_clear_outlier_snapshot"):
            st.session_state.outlier_snapshot = None
            st.info("Outlier snapshot cleared.")

    # Show before/after comparison if snapshot exists
    if st.session_state.get("outlier_snapshot"):
        snap = st.session_state.outlier_snapshot
        tracked_col = snap["column"]

        # Recalculate current outlier state for the same column
        if tracked_col in df.columns:
            curr_data = df[tracked_col].dropna()
            curr_outliers = int(
                (
                    (df[tracked_col] < snap["lower_bound"]) |
                    (df[tracked_col] > snap["upper_bound"])
                ).sum()
            )
            curr_rows = len(df)

            st.write("**Outlier Impact Comparison:**")

            cmp1, cmp2, cmp3, cmp4 = st.columns(4)
            cmp1.metric("Column",          tracked_col)
            cmp2.metric("Rows Before",     snap["row_count"],
                        delta=curr_rows - snap["row_count"])
            cmp3.metric("Outliers Before", snap["outlier_count"])
            cmp4.metric("Outliers After",  curr_outliers,
                        delta=curr_outliers - snap["outlier_count"])

            st.caption(
                f"Bounds used: Lower **{snap['lower_bound']}** · "
                f"Upper **{snap['upper_bound']}**"
            )
        else:
            st.info(
                f"Column `{tracked_col}` from snapshot no longer exists "
                "in the current dataset."
            )

# ---- Section 12: Remove Outlier Rows (IQR Method) ----
st.subheader("Remove Outlier Rows (IQR Method)")

st.write(
    "Select a numeric column and remove any rows where that column's value "
    "falls outside the IQR bounds (Q1 − 1.5×IQR or Q3 + 1.5×IQR). "
    "Rows with missing values in the selected column are not removed."
)

numeric_cols_for_removal = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_removal:
    st.info("No numeric columns found in the current dataset.")

else:
    outlier_removal_column = st.selectbox(
        label="Select a numeric column",
        options=numeric_cols_for_removal,
        key="outlier_removal_column"
    )

    if st.button("Remove Outliers", key="btn_remove_outliers_iqr"):

        updated_df, summary = remove_outliers_iqr(df, outlier_removal_column)

        if summary["Removed Count"] == 0:
            st.info(f"Nothing to change — no outliers found in `{outlier_removal_column}` using the IQR method.")

        else:
            # Save the updated dataframe to session state
            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="remove_outliers_iqr",
                columns=[outlier_removal_column],
                parameters={
                    "lower_bound": summary["Lower Bound"],
                    "upper_bound": summary["Upper Bound"],
                    "removed_count": summary["Removed Count"]
                }
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — removed **{summary['Removed Count']}** outlier row(s) from `{outlier_removal_column}`. Dataset now has **{len(updated_df)} rows × {updated_df.shape[1]} columns**.")
            set_last_action_summary("Remove Outliers", f"Removed {summary['Removed Count']} outlier row(s) from '{outlier_removal_column}'")
            st.rerun()

st.divider()

# ---- Section 12c: Before / After Scaling Statistics ----
st.subheader("Before / After Scaling Statistics")

st.write(
    "Take a snapshot of current column statistics before applying "
    "a scaling action. The comparison will appear automatically "
    "after scaling so you can verify the result."
)

numeric_cols_for_scale_snap = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_scale_snap:
    st.info("No numeric columns found in the current dataset.")

else:
    scale_snap_cols = st.multiselect(
        label="Select columns to track",
        options=numeric_cols_for_scale_snap,
        placeholder="Choose one or more numeric columns...",
        key="scaling_snapshot_columns"
    )

    snap_s_col1, snap_s_col2 = st.columns(2)

    with snap_s_col1:
        if st.button("📸 Take Scaling Snapshot", key="btn_take_scaling_snapshot"):

            if not scale_snap_cols:
                st.error("Please select at least one column to snapshot.")
            else:
                snapshot_data = {}
                for col in scale_snap_cols:
                    col_data = df[col].dropna()
                    snapshot_data[col] = {
                        "min":  round(float(col_data.min()),  4),
                        "max":  round(float(col_data.max()),  4),
                        "mean": round(float(col_data.mean()), 4),
                        "std":  round(float(col_data.std()),  4)
                    }
                st.session_state.scaling_snapshot = snapshot_data
                st.success(
                    f"✅ Snapshot taken for {len(scale_snap_cols)} column(s). "
                    "Apply a scaling action and return here to compare."
                )

    with snap_s_col2:
        if st.button("🗑 Clear Scaling Snapshot", key="btn_clear_scaling_snapshot"):
            st.session_state.scaling_snapshot = None
            st.info("Scaling snapshot cleared.")

    # Show before/after comparison if snapshot exists
    if st.session_state.get("scaling_snapshot"):
        snap = st.session_state.scaling_snapshot

        st.write("**Scaling Impact Comparison:**")

        for col, before_stats in snap.items():

            if col not in df.columns:
                st.caption(f"`{col}` no longer exists in the dataset.")
                continue

            curr_data = df[col].dropna()
            after_stats = {
                "min":  round(float(curr_data.min()),  4),
                "max":  round(float(curr_data.max()),  4),
                "mean": round(float(curr_data.mean()), 4),
                "std":  round(float(curr_data.std()),  4)
            }

            with st.expander(f"Column: `{col}`", expanded=True):
                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Min",
                    after_stats["min"],
                    delta=round(after_stats["min"] - before_stats["min"], 4)
                )
                c2.metric(
                    "Max",
                    after_stats["max"],
                    delta=round(after_stats["max"] - before_stats["max"], 4)
                )
                c3.metric(
                    "Mean",
                    after_stats["mean"],
                    delta=round(after_stats["mean"] - before_stats["mean"], 4)
                )
                c4.metric(
                    "Std",
                    after_stats["std"],
                    delta=round(after_stats["std"] - before_stats["std"], 4)
                )

                st.caption(
                    f"Before → Min: {before_stats['min']} · "
                    f"Max: {before_stats['max']} · "
                    f"Mean: {before_stats['mean']} · "
                    f"Std: {before_stats['std']}"
                )

# ---- Section 13: Min-Max Scaling ----
st.markdown('<a name="scaling"></a>', unsafe_allow_html=True)
st.subheader("Min-Max Scaling")

st.write(
    "Rescales selected numeric columns so that all values fall between 0 and 1. "
    "The formula used is: (value − min) / (max − min). "
    "This is useful before machine learning or when comparing columns with "
    "very different numeric ranges. Missing values are preserved as-is."
)

# Only offer numeric columns for scaling
numeric_cols_for_scaling = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_scaling:
    st.info("No numeric columns found in the current dataset.")

else:
    columns_to_scale = st.multiselect(
        label="Select numeric columns to scale",
        options=numeric_cols_for_scaling,
        placeholder="Choose one or more numeric columns...",
        key="minmax_scale_columns"
    )

    if st.button("Apply — Min-Max Scaling", key="btn_minmax_scale"):

        if not columns_to_scale:
            st.error("Please select at least one column.")

        else:
            updated_df = min_max_scale_columns(df, columns_to_scale)

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="min_max_scale_columns",
                columns=columns_to_scale,
                parameters={"method": "min-max", "range": "0 to 1"}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — Min-Max scaling applied to **{len(columns_to_scale)}** column(s). Values are now between 0 and 1.")
            set_last_action_summary("Min-Max Scaling", f"Scaled {len(columns_to_scale)} column(s)")
            st.rerun()

# ---- Section 14: Z-Score Standardization ----
st.subheader("Z-Score Standardization")

st.write(
    "Standardizes selected numeric columns so that each column has a "
    "mean of 0 and a standard deviation of 1. "
    "The formula used is: (value − mean) / std. "
    "This is useful when comparing columns with different units or scales. "
    "Missing values are preserved as-is."
)

# Only offer numeric columns for standardization
numeric_cols_for_zscore = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_zscore:
    st.info("No numeric columns found in the current dataset.")

else:
    columns_to_zscore = st.multiselect(
        label="Select numeric columns to standardize",
        options=numeric_cols_for_zscore,
        placeholder="Choose one or more numeric columns...",
        key="zscore_scale_columns"
    )

    if st.button("Apply — Z-Score Standardization", key="btn_zscore_scale"):

        if not columns_to_zscore:
            st.error("Please select at least one column.")

        else:
            updated_df = z_score_scale_columns(df, columns_to_zscore)

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="z_score_scale_columns",
                columns=columns_to_zscore,
                parameters={"method": "z-score", "mean": 0, "std": 1}
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(f"✅ Done — Z-score standardization applied to **{len(columns_to_zscore)}** column(s).")
            set_last_action_summary("Z-Score Standardization", f"Standardized {len(columns_to_zscore)} column(s)")
            st.rerun()

# ---- Section 15: Rename Column ----
st.markdown('<a name="column-operations"></a>', unsafe_allow_html=True)
st.subheader("Rename Column")

st.write(
    "Select a column and give it a new name. "
    "This is useful for making column names clearer or more consistent "
    "before exporting or visualizing the data."
)

column_to_rename = st.selectbox(
    label="Select a column to rename",
    options=df.columns.tolist(),
    key="rename_col_select"
)

new_column_name = st.text_input(
    label="New column name",
    placeholder="Enter a new name...",
    key="rename_col_new_name"
)

if st.button("Apply — Rename Column", key="btn_rename_column"):

    # Validate: new name must not be empty
    if new_column_name.strip() == "":
        st.error("Please enter a new column name.")

    # Validate: new name must not already exist in another column
    elif (
        new_column_name in df.columns
        and new_column_name != column_to_rename
    ):
        st.error(
            f"A column named `{new_column_name}` already exists. "
            "Please choose a different name."
        )

    # Validate: new name must actually be different
    elif new_column_name == column_to_rename:
        st.info("The new name is the same as the current name. Nothing was changed.")

    else:
        updated_df = rename_column(df, column_to_rename, new_column_name)

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="rename_column",
            columns=[column_to_rename],
            parameters={"old_name": column_to_rename, "new_name": new_column_name}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — column `{column_to_rename}` renamed to `{new_column_name}`.")
        set_last_action_summary("Rename Column", f"'{column_to_rename}' renamed to '{new_column_name}'")
        st.rerun()

# ---- Section 16: Drop Columns ----
st.subheader("Drop Columns")

st.write(
    "Select one or more columns to permanently remove from the dataset. "
    "Use this to eliminate columns that are irrelevant, redundant, or "
    "contain too many missing values to be useful."
)

columns_to_drop_cols = st.multiselect(
    label="Select columns to drop",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="drop_columns_select"
)

if st.button("Apply — Drop Selected Columns", key="btn_drop_columns"):

    if not columns_to_drop_cols:
        st.error("Please select at least one column.")

    else:
        updated_df = drop_columns(df, columns_to_drop_cols)

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="drop_columns",
            columns=columns_to_drop_cols,
            parameters={"columns_removed": len(columns_to_drop_cols)}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — dropped **{len(columns_to_drop_cols)}** column(s). Dataset now has **{len(updated_df)} rows × {updated_df.shape[1]} columns**.")
        set_last_action_summary("Drop Columns", f"Dropped {len(columns_to_drop_cols)} column(s)")
        st.rerun()

st.divider()

# ---- Section 16b: Bin Numeric Column into Categories ----
st.subheader("Bin Numeric Column into Categories")

st.write(
    "Convert a numeric column into grouped categories (bins). "
    "For example, an age column can become 'Low', 'Medium', 'High' bands. "
    "The result is saved as a new column alongside the original."
)

numeric_cols_for_bin = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_bin:
    st.info("No numeric columns found in the current dataset.")

else:
    bin_source_col = st.selectbox(
        label="Select a numeric column to bin",
        options=numeric_cols_for_bin,
        key="bin_source_column"
    )

    bin_count = st.slider(
        label="Number of bins",
        min_value=2,
        max_value=20,
        value=4,
        step=1,
        key="bin_count"
    )

    bin_output_col = st.text_input(
        label="New output column name",
        placeholder=f"e.g. {bin_source_col}_binned",
        key="bin_output_column"
    )

    # Preview bin ranges before applying
    usable_data = df[bin_source_col].dropna()

    if len(usable_data) >= bin_count:
        try:
            preview_bins = pd.cut(
                usable_data,
                bins=bin_count,
                include_lowest=True
            )
            st.caption(
                f"Preview — unique bin ranges that will be created: "
                f"{preview_bins.cat.categories.tolist()}"
            )
        except Exception:
            pass

    if st.button("Apply — Bin Column", key="btn_bin_column"):

        # Validation: output name must not be empty
        if bin_output_col.strip() == "":
            st.error("Please enter a name for the new output column.")

        # Validation: output name must not already exist
        elif bin_output_col.strip() in df.columns:
            st.error(
                f"A column named `{bin_output_col.strip()}` already exists. "
                "Please choose a different name."
            )

        # Validation: enough usable values to create bins
        elif len(usable_data) < bin_count:
            st.warning(
                f"⚠️ `{bin_source_col}` has only **{len(usable_data)}** "
                f"non-missing values — not enough to create {bin_count} bins. "
                "Try reducing the number of bins."
            )

        else:
            output_name = bin_output_col.strip()
            updated_df = df.copy()

            try:
                updated_df[output_name] = pd.cut(
                    updated_df[bin_source_col],
                    bins=bin_count,
                    include_lowest=True
                ).astype(str)   # convert to string so it works cleanly downstream

                # Save undo state and update session
                st.session_state.undo_stack = df.copy()
                st.session_state.working_df = updated_df

                log_entry = build_log_entry(
                    operation="bin_numeric_column",
                    columns=[bin_source_col],
                    parameters={
                        "bins": bin_count,
                        "output_column": output_name
                    }
                )
                st.session_state.transformation_log.append(log_entry)

                set_last_action_summary(
                    "Bin Numeric Column",
                    f"Binned `{bin_source_col}` into {bin_count} bins → `{output_name}`"
                )

                st.success(
                    f"✅ Done — `{bin_source_col}` binned into **{bin_count}** "
                    f"categories and saved as new column `{output_name}`. "
                    f"Dataset now has **{updated_df.shape[1]}** columns."
                )
                st.rerun()

            except Exception as e:
                st.error(f"Binning failed: {str(e)}")

st.divider()

# ---- Section 17: Create Calculated Column ----
st.subheader("Create Calculated Column")

st.write(
    "Create a new column by applying a simple arithmetic operation "
    "between two existing numeric columns. "
    "The result will be added as a new column to your dataset."
)

numeric_cols_for_calc = df.select_dtypes(include=["number"]).columns.tolist()

if len(numeric_cols_for_calc) < 2:
    st.info("You need at least two numeric columns to use this feature.")

else:
    calc_col_a = st.selectbox(
        label="First column",
        options=numeric_cols_for_calc,
        key="calc_col_a"
    )

    calc_operation = st.selectbox(
        label="Operation",
        options=["add", "subtract", "multiply", "divide"],
        key="calc_operation"
    )

    calc_col_b = st.selectbox(
        label="Second column",
        options=numeric_cols_for_calc,
        key="calc_col_b"
    )

    calc_new_col_name = st.text_input(
        label="New column name",
        placeholder="e.g. revenue_per_unit",
        key="calc_new_col_name"
    )

    if st.button("Apply — Create Calculated Column", key="btn_create_calc_col"):

        if calc_new_col_name.strip() == "":
            st.error("Please enter a name for the new column.")

        elif calc_new_col_name in df.columns:
            st.error(
                f"A column named `{calc_new_col_name}` already exists. "
                "Please choose a different name."
            )

        else:
            updated_df = create_calculated_column(
                df,
                col_a=calc_col_a,
                operation=calc_operation,
                col_b=calc_col_b,
                new_col_name=calc_new_col_name
            )

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="create_calculated_column",
                columns=[calc_col_a, calc_col_b],
                parameters={
                    "operation": calc_operation,
                    "new_column": calc_new_col_name
                }
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(
                f"New column `{calc_new_col_name}` created using: "
                f"`{calc_col_a}` {calc_operation} `{calc_col_b}`."
            )
            st.rerun()

st.divider()

# ---- Section 18: Merge Columns ----
st.subheader("Merge Columns")

st.write(
    "Combine two columns into a single new text column. "
    "Both columns will be converted to text and joined together "
    "using a separator you choose — for example a space, dash, or underscore."
)

all_cols_for_merge = df.columns.tolist()

merge_col_a = st.selectbox(
    label="First column",
    options=all_cols_for_merge,
    key="merge_col_a"
)

merge_col_b = st.selectbox(
    label="Second column",
    options=all_cols_for_merge,
    key="merge_col_b"
)

merge_separator = st.text_input(
    label="Separator",
    value=" ",
    help="Text to place between the two values. Default is a space.",
    key="merge_separator"
)

merge_new_col_name = st.text_input(
    label="New column name",
    placeholder="e.g. full_name",
    key="merge_new_col_name"
)

if st.button("Apply — Merge Columns", key="btn_merge_columns"):

    if merge_new_col_name.strip() == "":
        st.error("Please enter a name for the new column.")

    elif merge_new_col_name in df.columns:
        st.error(
            f"A column named `{merge_new_col_name}` already exists. "
            "Please choose a different name."
        )

    else:
        updated_df = merge_columns(
            df,
            col_a=merge_col_a,
            col_b=merge_col_b,
            separator=merge_separator,
            new_col_name=merge_new_col_name
        )

        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="merge_columns",
            columns=[merge_col_a, merge_col_b],
            parameters={
                "separator": repr(merge_separator),
                "new_column": merge_new_col_name
            }
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(
            f"New column `{merge_new_col_name}` created by merging "
            f"`{merge_col_a}` and `{merge_col_b}` "
            f"with separator: `{repr(merge_separator)}`."
        )
        st.rerun()

st.divider()

# ---- Section 19: Split Column ----
st.subheader("Split Column")

st.write(
    "Split one column into multiple new columns using a separator. "
    "For example, splitting a 'full_name' column on a space would "
    "create 'name_1' and 'name_2'. "
    "The original column is kept unchanged."
)

split_col_options = df.columns.tolist()

split_column_select = st.selectbox(
    label="Select column to split",
    options=split_col_options,
    key="split_col_select"
)

split_separator = st.text_input(
    label="Separator",
    value=" ",
    help="The character or text to split on. Default is a space.",
    key="split_separator"
)

split_base_name = st.text_input(
    label="Base name for new columns",
    placeholder="e.g. name → name_1, name_2 ...",
    key="split_base_name"
)

if st.button("Apply — Split Column", key="btn_split_column"):

    if split_base_name.strip() == "":
        st.error("Please enter a base name for the new columns.")

    else:
        # Check in advance how many columns would be created
        preview_split = df[split_column_select].astype(str).str.split(
            split_separator, expand=True
        )
        proposed_names = [
            f"{split_base_name}_{i + 1}"
            for i in range(preview_split.shape[1])
        ]

        # Check if any proposed name already exists in the dataframe
        conflicts = [name for name in proposed_names if name in df.columns]

        if conflicts:
            st.error(
                f"The following column names already exist: "
                f"{', '.join(conflicts)}. "
                "Please choose a different base name."
            )

        else:
            updated_df, new_col_names = split_column(
                df,
                column=split_column_select,
                separator=split_separator,
                base_name=split_base_name
            )

            st.session_state.undo_stack = df.copy()
            st.session_state.working_df = updated_df

            log_entry = build_log_entry(
                operation="split_column",
                columns=[split_column_select],
                parameters={
                    "separator": repr(split_separator),
                    "new_columns": new_col_names
                }
            )
            st.session_state.transformation_log.append(log_entry)

            st.success(
                f"Column `{split_column_select}` split into "
                f"**{len(new_col_names)}** new column(s): "
                f"{', '.join(new_col_names)}."
            )
            st.rerun()

st.divider()

# ====================================================================
# VALIDATION RULES
# ====================================================================

st.header("Validation Rules")

st.write(
    "These tools check your data for quality issues without changing anything. "
    "No transformations are applied and nothing is logged — "
    "these are read-only checks to help you understand your data."
)

st.divider()

# ---- Validation 1: Check Uniqueness ----
st.subheader("Check Uniqueness")

st.write(
    "Select one or more columns and check whether their values are unique "
    "across every row. This is useful for validating ID columns or "
    "detecting unexpected duplicates in key fields."
)

uniqueness_cols = st.multiselect(
    label="Select columns to check",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="uniqueness_check_cols"
)

if st.button("Run Uniqueness Check", key="btn_check_uniqueness"):

    if not uniqueness_cols:
        st.error("Please select at least one column.")

    else:
        # Find rows that are duplicated across the selected columns
        duplicate_mask = df.duplicated(subset=uniqueness_cols, keep=False)
        duplicate_rows = df[duplicate_mask]
        duplicate_count = int(df.duplicated(subset=uniqueness_cols).sum())

        if duplicate_count == 0:
            st.success(
                f"All values are unique across the selected column(s): "
                f"{', '.join(uniqueness_cols)}."
            )

        else:
            st.warning(
                f"Found **{duplicate_count}** duplicate combination(s) "
                f"across: {', '.join(uniqueness_cols)}."
            )

            st.write(
                f"Showing up to **10** of the **{len(duplicate_rows)}** "
                "rows involved in duplications:"
            )

            st.dataframe(
                duplicate_rows.head(10),
                use_container_width=True
            )

st.divider()

# ---- Validation 2: Check Missing Values ----
st.subheader("Check Missing Values")

st.write(
    "Select one or more columns to check how many missing values they contain. "
    "This is a read-only check — nothing will be changed in your dataset."
)

missing_check_cols = st.multiselect(
    label="Select columns to check",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="missing_check_cols"
)

if st.button("Run Missing Values Check", key="btn_check_missing"):

    if not missing_check_cols:
        st.error("Please select at least one column.")

    else:
        total_rows = len(df)

        # Build a summary table for the selected columns only
        results = []
        for col in missing_check_cols:
            missing_count = int(df[col].isnull().sum())
            missing_pct = round(missing_count / total_rows * 100, 2)
            results.append({
                "Column": col,
                "Missing Count": missing_count,
                "Missing (%)": missing_pct
            })

        results_df = pd.DataFrame(results)
        results_df.index = range(1, len(results_df) + 1)

        # Check if any column actually has missing values
        total_missing = results_df["Missing Count"].sum()

        if total_missing == 0:
            st.success(
                "No missing values found in the selected column(s): "
                f"{', '.join(missing_check_cols)}."
            )
        else:
            st.warning(
                f"Missing values detected across the selected column(s). "
                f"See details below."
            )

        st.dataframe(results_df, use_container_width=True)
        
st.divider()

# ---- Validation 3: Check Numeric Range ----
st.subheader("Check Numeric Range")

st.write(
    "Select a numeric column and define an allowed minimum and maximum value. "
    "Any rows that fall outside that range will be shown below. "
    "This is a read-only check — nothing will be changed in your dataset."
)

numeric_cols_for_range = df.select_dtypes(include=["number"]).columns.tolist()

if not numeric_cols_for_range:
    st.info("No numeric columns found in the current dataset.")

else:
    range_check_col = st.selectbox(
        label="Select a numeric column",
        options=numeric_cols_for_range,
        key="range_check_col"
    )

    range_col1, range_col2 = st.columns(2)

    with range_col1:
        range_min = st.number_input(
            label="Minimum allowed value",
            value=0.0,
            key="range_check_min"
        )

    with range_col2:
        range_max = st.number_input(
            label="Maximum allowed value",
            value=100.0,
            key="range_check_max"
        )

    if st.button("Run Range Check", key="btn_check_range"):

        if range_min > range_max:
            st.error(
                "Minimum value cannot be greater than maximum value. "
                "Please correct the range and try again."
            )

        else:
            # Ignore missing values — they are not range violations
            col_data = df[range_check_col].dropna()

            out_of_range_mask = (
                (df[range_check_col] < range_min) |
                (df[range_check_col] > range_max)
            )

            out_of_range_rows = df[out_of_range_mask]
            out_of_range_count = len(out_of_range_rows)

            if out_of_range_count == 0:
                st.success(
                    f"All values in `{range_check_col}` are within the "
                    f"allowed range of {range_min} to {range_max}."
                )

            else:
                st.warning(
                    f"Found **{out_of_range_count}** row(s) in "
                    f"`{range_check_col}` outside the range "
                    f"{range_min} to {range_max}."
                )

                st.write(
                    f"Showing up to **10** of the **{out_of_range_count}** "
                    "out-of-range rows:"
                )

                st.dataframe(
                    out_of_range_rows.head(10),
                    use_container_width=True
                )
  
st.divider()

# ---- Validation 4: Check Allowed Values ----
st.markdown('<a name="validation"></a>', unsafe_allow_html=True)
st.subheader("Validation Rules")
st.write(
    "Use these tools to check data quality without modifying your dataset."
)
st.divider()
st.subheader("Check Allowed Values")

st.write(
    "Select a column and enter a list of allowed values separated by commas. "
    "Any row whose value is not on that list will be flagged below. "
    "This is a read-only check — nothing will be changed in your dataset."
)

allowed_check_col = st.selectbox(
    label="Select a column to check",
    options=df.columns.tolist(),
    key="allowed_check_col"
)

allowed_values_input = st.text_input(
    label="Allowed values (comma-separated)",
    placeholder="e.g. Yes, No, Maybe",
    key="allowed_values_input"
)

if st.button("Run Allowed Values Check", key="btn_check_allowed"):

    if allowed_values_input.strip() == "":
        st.error("Please enter at least one allowed value.")

    else:
        # Split on commas and strip whitespace from each entry
        allowed_list = [
            v.strip() for v in allowed_values_input.split(",")
            if v.strip() != ""
        ]

        # Convert column to string for safe comparison, but keep NaN as NaN
        # We check only non-missing rows
        non_missing_mask = df[allowed_check_col].notna()
        col_as_str = df.loc[non_missing_mask, allowed_check_col].astype(str)

        # Find rows where the value is not in the allowed list
        invalid_mask = non_missing_mask & ~df[allowed_check_col].astype(str).isin(allowed_list)
        invalid_rows = df[invalid_mask]
        invalid_count = len(invalid_rows)

        if invalid_count == 0:
            st.success(
                f"All non-missing values in `{allowed_check_col}` "
                f"match the allowed values: {', '.join(allowed_list)}."
            )

        else:
            st.warning(
                f"Found **{invalid_count}** row(s) in `{allowed_check_col}` "
                f"with values not in the allowed list."
            )

            st.write(
                f"Showing up to **10** of the **{invalid_count}** "
                "rows with invalid values:"
            )

            st.dataframe(
                invalid_rows.head(10),
                use_container_width=True
            )

st.divider()

# ---- Validation: Non-Null Constraint Check ----
st.subheader("Non-Null Constraint Check")

st.write(
    "Select one or more columns that must not contain missing values. "
    "This check will flag any column that violates the non-null requirement. "
    "Your dataset is not modified."
)

non_null_check_cols = st.multiselect(
    label="Select required (non-null) columns",
    options=df.columns.tolist(),
    placeholder="Choose one or more columns...",
    key="non_null_check_columns"
)

if st.button("Check Non-Null Constraint", key="btn_check_non_null"):

    if not non_null_check_cols:
        st.error("Please select at least one column to check.")

    else:
        total_rows = len(df)
        violations = []

        for col in non_null_check_cols:
            missing_count = int(df[col].isnull().sum())
            if missing_count > 0:
                missing_pct = round(missing_count / total_rows * 100, 2)
                violations.append({
                    "Column":           col,
                    "Missing Count":    missing_count,
                    "Missing (%)":      missing_pct
                })

        if not violations:
            st.success(
                f"✅ All **{len(non_null_check_cols)}** selected column(s) "
                "pass the non-null constraint — no missing values found."
            )
            # Clear any previous violations since this check passed
            st.session_state.validation_violations_df = None
        else:
            st.warning(
                f"⚠️ **{len(violations)}** column(s) violate the non-null "
                "constraint. See details below:"
            )
            violations_df = pd.DataFrame(violations)
            violations_df.index = range(1, len(violations_df) + 1)
            st.dataframe(violations_df, use_container_width=True)
            # Save violations so the shared export section can use them
            st.session_state.validation_violations_df = violations_df

st.divider()

# ---- Validation: Check Datetime Parse Readiness ----
st.markdown('<a name="validation-datetime"></a>', unsafe_allow_html=True)
st.subheader("Check Datetime Parse Readiness")

st.write(
    "Select a column to check whether its values can be parsed as dates or timestamps. "
    "This is useful before converting a column to datetime type. "
    "Missing values are ignored. Your dataset is not modified."
)

datetime_check_column = st.selectbox(
    label="Select a column to check",
    options=df.columns.tolist(),
    key="datetime_check_column"
)

if st.button("Check Datetime Readiness", key="btn_check_datetime"):

    # Work only on non-missing values
    col_non_null = df[datetime_check_column].dropna()
    total_checked = len(col_non_null)

    if total_checked == 0:
        st.info("The selected column has no non-missing values to check.")

    else:
        # Try parsing each value — errors="coerce" turns failures into NaT
        parsed = pd.to_datetime(col_non_null, errors="coerce")

        # Successfully parsed = not NaT after conversion
        success_count = int(parsed.notna().sum())
        failed_count = total_checked - success_count
        success_pct = round((success_count / total_checked) * 100, 1)

        # Show summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Checked", total_checked)
        col2.metric("Parseable", success_count)
        col3.metric("Failed", failed_count)
        col4.metric("Success Rate", f"{success_pct}%")

        st.divider()

        if failed_count == 0:
            st.success(
                f"All **{total_checked}** non-missing values in "
                f"`{datetime_check_column}` can be parsed as datetime."
            )
        else:
            st.warning(
                f"**{failed_count}** value(s) could not be parsed as datetime. "
                "Preview below (up to 10 rows):"
            )

            # Find the rows in the original df where parsing failed
            # We use the same index as col_non_null to align correctly
            failed_index = parsed[parsed.isna()].index
            failed_rows = df.loc[failed_index]

            st.dataframe(failed_rows.head(10), use_container_width=True)

st.divider()

# ---- Validation: Export Validation Violations as CSV ----
st.subheader("Export Validation Violations")

st.write(
    "If a validation check above produced a violations table, "
    "you can download it here as a CSV file for review or reporting. "
    "Run a validation check first to make the export available."
)

violations_export = st.session_state.get("validation_violations_df")

if violations_export is None or violations_export.empty:
    st.info(
        "No violations table available yet. "
        "Run a validation check above that finds violations first."
    )
else:
    st.success(
        f"**{len(violations_export)}** violation(s) ready to export."
    )
    st.dataframe(violations_export, use_container_width=True)

    violations_csv = violations_export.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇ Download Violations as CSV",
        data=violations_csv,
        file_name="validation_violations.csv",
        mime="text/csv",
        key="download_violations_csv"
    )              

st.divider()

# ---- Transformation Log ----

st.subheader("Transformation Log")

st.write(
    "Every cleaning action you apply is recorded here in order. "
    "Use this to keep track of what has been done to the dataset."
)

log = st.session_state.transformation_log

if not log:
    st.info("No transformations recorded yet.")

else:
    st.success(f"**{len(log)}** transformation(s) recorded so far.")

    # Display each log entry as a numbered item
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

    # Button to clear the log without touching the dataframe
    if st.button("Clear Transformation Log", key="btn_clear_log"):
        st.session_state.transformation_log = []
        st.success("Transformation log cleared.")
        st.rerun()

st.divider()

# ---- Current Cleaned Data Preview ----
st.markdown('<a name="preview"></a>', unsafe_allow_html=True)
st.subheader("Current Cleaned Data Preview")

st.write(
    "This shows the current state of your working dataset after all cleaning actions applied so far."
)

preview_df = st.session_state.working_df

# Show shape info
preview_rows, preview_cols = preview_df.shape
st.caption(f"Current shape: **{preview_rows} rows × {preview_cols} columns**")

# Let user pick how many rows to preview
row_count = st.selectbox(
    label="Number of rows to preview",
    options=[5, 10, 20, 50],
    index=1,  # default to 10
    key="preview_row_count"
)

st.dataframe(preview_df.head(row_count), use_container_width=True)

# --- Placeholder for more cleaning tools (coming in next steps) ---
st.info("More cleaning and validation tools will be added here soon.")