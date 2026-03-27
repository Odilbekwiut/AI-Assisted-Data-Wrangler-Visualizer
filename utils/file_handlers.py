import pandas as pd


def detect_file_type(uploaded_file):
    """
    Looks at the file name and returns the file type as a lowercase string.
    Returns "csv", "xlsx", or "json".
    Returns None if the file type is not recognised.
    """
    name = uploaded_file.name.lower()

    if name.endswith(".csv"):
        return "csv"
    elif name.endswith(".xlsx"):
        return "xlsx"
    elif name.endswith(".json"):
        return "json"
    else:
        return None


def load_csv(uploaded_file):
    """
    Loads a CSV file into a pandas DataFrame.
    Returns the DataFrame or raises an error if it fails.
    """
    return pd.read_csv(uploaded_file)


def load_xlsx(uploaded_file):
    """
    Loads an XLSX file into a pandas DataFrame.
    Reads the first sheet by default.
    Returns the DataFrame or raises an error if it fails.
    """
    return pd.read_excel(uploaded_file, engine="openpyxl")


def load_json(uploaded_file):
    """
    Loads a JSON file into a pandas DataFrame.
    Expects the JSON to be in a tabular format (list of records or columns).
    Returns the DataFrame or raises an error if it fails.
    """
    return pd.read_json(uploaded_file)


def load_uploaded_file(uploaded_file):
    """
    Main loader function.
    Detects the file type, calls the right loader, and returns three values:
      - dataframe : the loaded data (or None if loading failed)
      - file_type : "csv", "xlsx", or "json" (or None)
      - error_message : a helpful string if something went wrong (or None)

    Always use this function from the upload page — do not call the
    individual loaders directly from the UI code.
    """

    # Step 1 — detect the file type from the file name
    file_type = detect_file_type(uploaded_file)

    # Step 2 — if file type is not supported, return an error immediately
    if file_type is None:
        return None, None, "Unsupported file type. Please upload a CSV, XLSX, or JSON file."

    # Step 3 — try to load the file using the correct loader
    try:
        if file_type == "csv":
            df = load_csv(uploaded_file)
        elif file_type == "xlsx":
            df = load_xlsx(uploaded_file)
        elif file_type == "json":
            df = load_json(uploaded_file)

        # Step 4 — basic check: the file loaded but is completely empty
        if df.empty:
            return None, file_type, "The file loaded successfully but contains no data."

        # Step 5 — everything worked, return the dataframe and file type
        return df, file_type, None

    except Exception as e:
        # If anything went wrong during loading, return a helpful message
        # str(e) gives us the actual error detail from pandas
        return None, file_type, f"Failed to load file: {str(e)}"