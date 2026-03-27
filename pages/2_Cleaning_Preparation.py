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

if st.button("Apply — Convert Types", key="btn_convert_types"):

    if not columns_to_convert:
        st.error("Please select at least one column.")

    else:
        updated_df = convert_column_types(df, columns_to_convert, target_type)
        st.session_state.undo_stack = df.copy()
        st.session_state.working_df = updated_df

        log_entry = build_log_entry(
            operation="convert_column_types",
            columns=columns_to_convert,
            parameters={"target_type": target_type}
        )
        st.session_state.transformation_log.append(log_entry)

        st.success(f"✅ Done — converted **{len(columns_to_convert)}** column(s) to `{target_type}`.")
        set_last_action_summary("Convert Types", f"Converted {len(columns_to_convert)} column(s) to {target_type}")
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