import pandas as pd
import streamlit as st


@st.cache_data
def get_shape_info(df):
    """
    Returns the number of rows and columns as a tuple.
    Example: (150, 8)
    """
    rows, columns = df.shape
    return rows, columns


@st.cache_data
def get_column_dtype_summary(df):
    """
    Returns a DataFrame with each column name and its pandas data type.
    """
    summary = pd.DataFrame({
        "Column Name": df.columns,
        "Data Type": df.dtypes.values
    })
    summary.index = range(1, len(summary) + 1)
    return summary


@st.cache_data
def get_missing_values_summary(df):
    """
    Returns a DataFrame showing missing value counts and percentages.
    Only includes columns that have at least one missing value.
    Returns an empty DataFrame if no missing values exist.
    """
    total_rows = len(df)
    missing_count = df.isnull().sum()
    missing_percent = (missing_count / total_rows * 100).round(2)

    summary = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing Percent (%)": missing_percent.values
    })

    summary = summary[summary["Missing Count"] > 0]
    summary.index = range(1, len(summary) + 1)
    return summary


@st.cache_data
def get_duplicate_count(df):
    """
    Returns the number of fully duplicate rows as an integer.
    """
    return int(df.duplicated().sum())


@st.cache_data
def get_numeric_summary(df):
    """
    Returns descriptive statistics for numeric columns only.
    Result is transposed so each row represents one numeric column.
    Returns an empty DataFrame if no numeric columns exist.
    """
    numeric_df = df.select_dtypes(include=["number"])

    if numeric_df.empty:
        return pd.DataFrame()

    summary = numeric_df.describe().T.round(2)
    summary.index.name = "Column"
    return summary


@st.cache_data
def get_categorical_summary(df):
    """
    Returns a summary of object and category columns only.
    Includes non-null count, unique count, most frequent value and its count.
    Returns an empty DataFrame if no categorical columns exist.
    """
    cat_df = df.select_dtypes(include=["object", "category"])

    if cat_df.empty:
        return pd.DataFrame()

    rows = []

    for col in cat_df.columns:
        series = cat_df[col]
        non_null_count = int(series.notna().sum())
        unique_count = int(series.nunique())
        value_counts = series.value_counts()

        if not value_counts.empty:
            most_frequent = value_counts.index[0]
            most_frequent_count = int(value_counts.iloc[0])
        else:
            most_frequent = "N/A"
            most_frequent_count = 0

        rows.append({
            "Column": col,
            "Non-Null Count": non_null_count,
            "Unique Values": unique_count,
            "Most Frequent": most_frequent,
            "Most Frequent Count": most_frequent_count
        })

    summary = pd.DataFrame(rows)
    summary.index = range(1, len(summary) + 1)
    return summary