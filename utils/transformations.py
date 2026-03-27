import pandas as pd
from datetime import datetime


def fill_missing_with_constant(df, columns, fill_value):
    """
    Fills missing values in the selected columns with a constant value.
    """
    df = df.copy()

    for col in columns:
        try:
            if pd.api.types.is_numeric_dtype(df[col]):
                typed_value = pd.to_numeric(fill_value)
            else:
                typed_value = fill_value
        except (ValueError, TypeError):
            typed_value = fill_value

        df[col] = df[col].fillna(typed_value)

    return df


def drop_rows_with_missing(df, columns):
    """
    Drops any rows that have a missing value in at least one of the selected columns.
    """
    df = df.copy()
    df = df.dropna(subset=columns)
    df = df.reset_index(drop=True)
    return df


def remove_full_row_duplicates(df, keep="first"):
    """
    Removes fully duplicate rows where every column value matches another row.
    """
    df = df.copy()
    df = df.drop_duplicates(keep=keep)
    df = df.reset_index(drop=True)
    return df


def remove_duplicates_by_columns(df, columns, keep="first"):
    """
    Removes duplicate rows based only on the selected columns.
    """
    df = df.copy()
    df = df.drop_duplicates(subset=columns, keep=keep)
    df = df.reset_index(drop=True)
    return df


def convert_column_types(df, columns, target_type):
    """
    Converts selected columns to the chosen data type.
    Supports: "string", "category", "numeric", "datetime"
    """
    df = df.copy()

    for col in columns:
        if target_type == "string":
            df[col] = df[col].astype(str)

        elif target_type == "category":
            df[col] = df[col].astype("category")

        elif target_type == "numeric":
            df[col] = pd.to_numeric(df[col], errors="coerce")

        elif target_type == "datetime":
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


def standardize_text_case(df, columns, case_method):
    """
    Converts text values in the selected columns to a consistent case.

    Parameters:
      df          : the current working dataframe
      columns     : list of column names to apply case conversion to
      case_method : "lower" converts all text to lowercase
                    "title" converts text to Title Case (first letter of each word)

    Important:
      Missing values (NaN) are preserved as NaN.
      Without careful handling, applying .str.lower() would turn NaN into
      the string "nan" which looks like real data but is not.

    Returns:
      A new dataframe with text case standardized in the selected columns.
    """
    df = df.copy()

    for col in columns:
        if case_method == "lower":
            # .str.lower() works on the string accessor and safely keeps NaN as NaN
            df[col] = df[col].str.lower()

        elif case_method == "title":
            # .str.title() capitalizes the first letter of every word
            df[col] = df[col].str.title()

    return df

def replace_values_in_columns(df, columns, old_value, new_value):
    """
    Replaces exact matches of old_value with new_value in the selected columns.

    Parameters:
      df        : the current working dataframe
      columns   : list of column names to apply the replacement to
      old_value : the value to search for (as a string)
      new_value : the value to replace it with (as a string)

    Returns:
      A new dataframe with the replacements applied.
    """
    df = df.copy()

    for col in columns:
        # Replace only exact matches — other values are left unchanged
        df[col] = df[col].replace(old_value, new_value)

    return df

def group_rare_categories(df, column, min_frequency):
    """
    Replaces category values that appear less than min_frequency times with "Other".
    Missing values are left unchanged.

    Parameters:
      df            : the current working dataframe
      column        : the column name to apply grouping to
      min_frequency : values appearing fewer times than this become "Other"

    Returns:
      A new dataframe with rare categories grouped.
    """
    df = df.copy()

    # Count how many times each value appears in the column
    value_counts = df[column].value_counts()

    # Find values that appear less than the minimum frequency
    rare_values = value_counts[value_counts < min_frequency].index

    # Replace rare values with "Other" but leave NaN untouched
    df[column] = df[column].apply(
        lambda x: "Other" if x in rare_values else x
    )

    return df

def analyze_outliers_iqr(df, column):
    """
    Analyzes outliers in a single numeric column using the IQR method.

    The IQR (Interquartile Range) method defines outliers as values that fall
    below Q1 - 1.5*IQR or above Q3 + 1.5*IQR.

    Parameters:
      df     : the current working dataframe
      column : the numeric column name to analyze

    Returns:
      summary      : a dictionary with Q1, Q3, IQR, bounds, and outlier count
      outlier_rows : a dataframe containing only the rows identified as outliers
    """
    # Drop missing values before calculating so they don't affect the results
    col_data = df[column].dropna()

    q1 = col_data.quantile(0.25)
    q3 = col_data.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # A row is an outlier if its value is outside the lower or upper bound
    outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
    outlier_rows = df[outlier_mask].copy()

    summary = {
        "Q1": round(q1, 4),
        "Q3": round(q3, 4),
        "IQR": round(iqr, 4),
        "Lower Bound": round(lower_bound, 4),
        "Upper Bound": round(upper_bound, 4),
        "Outlier Count": len(outlier_rows)
    }

    return summary, outlier_rows

def remove_outliers_iqr(df, column):
    """
    Removes rows where the selected numeric column is an outlier
    using the IQR method.

    Parameters:
      df     : the current working dataframe
      column : the numeric column name to use for outlier detection

    Returns:
      updated_df : dataframe with outlier rows removed
      summary    : dictionary with IQR values and removed row count
    """
    df = df.copy()

    # Drop missing values only for the calculation — they are not outliers
    col_data = df[column].dropna()

    q1 = col_data.quantile(0.25)
    q3 = col_data.quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    # Keep rows that are within bounds OR have a missing value in this column
    # Missing values are not outliers and should not be removed here
    mask_keep = (
        (df[column] >= lower_bound) & (df[column] <= upper_bound)
    ) | df[column].isna()

    removed_count = int((~mask_keep).sum())
    updated_df = df[mask_keep].reset_index(drop=True)

    summary = {
        "Q1": round(q1, 4),
        "Q3": round(q3, 4),
        "IQR": round(iqr, 4),
        "Lower Bound": round(lower_bound, 4),
        "Upper Bound": round(upper_bound, 4),
        "Removed Count": removed_count
    }

    return updated_df, summary

def min_max_scale_columns(df, columns):
    """
    Applies Min-Max scaling to the selected numeric columns.

    Each value is scaled using the formula: (value - min) / (max - min)
    This transforms all values to a range between 0 and 1.

    Parameters:
      df      : the current working dataframe
      columns : list of numeric column names to scale

    Notes:
      - If a column has the same min and max (all values identical),
        it is left unchanged to avoid dividing by zero.
      - Missing values remain as NaN after scaling.

    Returns:
      A new dataframe with the selected columns scaled.
    """
    df = df.copy()

    for col in columns:
        col_min = df[col].min()
        col_max = df[col].max()

        # Guard against division by zero when all values are the same
        if col_max == col_min:
            continue  # Leave this column unchanged

        df[col] = (df[col] - col_min) / (col_max - col_min)

    return df

def z_score_scale_columns(df, columns):
    """
    Applies Z-score standardization to the selected numeric columns.

    Each value is scaled using the formula: (value - mean) / std
    This transforms values so the column has a mean of 0 and std of 1.

    Parameters:
      df      : the current working dataframe
      columns : list of numeric column names to standardize

    Notes:
      - If a column has a standard deviation of 0 (all values identical),
        it is left unchanged to avoid dividing by zero.
      - Missing values remain as NaN after standardization.

    Returns:
      A new dataframe with the selected columns standardized.
    """
    df = df.copy()

    for col in columns:
        col_mean = df[col].mean()
        col_std = df[col].std()

        # Guard against division by zero when all values are identical
        if col_std == 0:
            continue  # Leave this column unchanged

        df[col] = (df[col] - col_mean) / col_std

    return df

def rename_column(df, old_name, new_name):
    """
    Renames a single column in the dataframe.

    Parameters:
      df       : the current working dataframe
      old_name : the current name of the column
      new_name : the new name to give the column

    Returns:
      A new dataframe with the column renamed.
    """
    df = df.copy()

    # df.rename() takes a dictionary mapping old name to new name
    df = df.rename(columns={old_name: new_name})

    return df

def drop_columns(df, columns):
    """
    Drops the selected columns from the dataframe.

    Parameters:
      df      : the current working dataframe
      columns : list of column names to remove

    Returns:
      A new dataframe with the selected columns removed.
    """
    df = df.copy()

    # axis=1 tells pandas we are dropping columns, not rows
    df = df.drop(columns=columns, axis=1)

    return df

def create_calculated_column(df, col_a, operation, col_b, new_col_name):
    """
    Creates a new column by applying an arithmetic operation
    between two existing numeric columns.

    For divide, zeros in col_b are replaced with NaN to avoid
    division by zero errors.

    Parameters:
      df           : the current working dataframe
      col_a        : name of the first numeric column
      operation    : one of "add", "subtract", "multiply", "divide"
      col_b        : name of the second numeric column
      new_col_name : name to give the new column

    Returns:
      A new dataframe with the calculated column appended.
    """
    df = df.copy()

    if operation == "add":
        df[new_col_name] = df[col_a] + df[col_b]

    elif operation == "subtract":
        df[new_col_name] = df[col_a] - df[col_b]

    elif operation == "multiply":
        df[new_col_name] = df[col_a] * df[col_b]

    elif operation == "divide":
        # Replace zeros with NaN before dividing to avoid ZeroDivisionError
        df[new_col_name] = df[col_a].div(
            df[col_b].replace(0, float("nan"))
        )

    return df

def merge_columns(df, col_a, col_b, separator, new_col_name):
    """
    Merges two columns into a new column by converting both to strings
    and joining them with a separator.

    Parameters:
      df           : the current working dataframe
      col_a        : name of the first column
      col_b        : name of the second column
      separator    : string to place between the two values (e.g. " " or "-")
      new_col_name : name to give the new merged column

    Returns:
      A new dataframe with the merged column appended.
    """
    df = df.copy()

    # Convert both columns to string first so any data type can be merged safely
    # .astype(str) turns numbers, dates, etc. into plain text before joining
    df[new_col_name] = df[col_a].astype(str) + separator + df[col_b].astype(str)

    return df

def split_column(df, column, separator, base_name):
    """
    Splits a single column into multiple new columns using a separator.

    The original column is left unchanged. New columns are named
    base_name_1, base_name_2, base_name_3, and so on.

    Parameters:
      df        : the current working dataframe
      column    : the column to split
      separator : the string to split on (e.g. " " or ",")
      base_name : prefix for the new column names

    Returns:
      A new dataframe with the split columns appended.
    """
    df = df.copy()

    # Convert to string first so numbers or mixed types do not cause errors
    split_result = df[column].astype(str).str.split(separator, expand=True)

    # Name new columns as base_name_1, base_name_2, etc.
    split_result.columns = [
        f"{base_name}_{i + 1}" for i in range(split_result.shape[1])
    ]

    # Join the new columns onto the existing dataframe
    df = pd.concat([df, split_result], axis=1)

    return df, split_result.columns.tolist()





def build_log_entry(operation, columns, parameters):
    """
    Builds a single transformation log entry as a dictionary.
    Used by every cleaning action to keep logging consistent.
    """
    return {
        "operation": operation,
        "columns": columns,
        "parameters": parameters,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }