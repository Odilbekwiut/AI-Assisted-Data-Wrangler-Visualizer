def build_report_text(transformation_log, file_name=None):
    """
    Builds a human-readable transformation report as a single string.

    Used by both the report preview and the TXT download button so that
    what the user sees on screen matches what they download exactly.

    Parameters:
      transformation_log : list of dicts from st.session_state.transformation_log
      file_name          : the uploaded file name (optional, shown in header)

    Returns:
      A plain-text string ready to display or write to a .txt file.
    """
    from datetime import datetime

    lines = []

    # --- Report Header ---
    lines.append("=" * 60)
    lines.append("  TRANSFORMATION REPORT")
    lines.append("  AI-Assisted Data Wrangler & Visualizer")
    lines.append("=" * 60)

    # Show the file name if we have one
    if file_name:
        lines.append(f"Dataset : {file_name}")
    else:
        lines.append("Dataset : Not recorded")

    # Stamp when this report was generated (not when steps ran — that is per step)
    lines.append(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Total Steps : {len(transformation_log)}")
    lines.append("=" * 60)

    # --- No steps recorded ---
    if not transformation_log:
        lines.append("")
        lines.append("No transformations have been applied in this session.")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    # --- One block per transformation step ---
    for i, entry in enumerate(transformation_log, start=1):

        lines.append("")
        lines.append(f"Step {i}")
        lines.append("-" * 40)

        # Operation name — always present
        operation = entry.get("operation", "Unknown operation")
        lines.append(f"  Operation  : {operation}")

        # Timestamp — recorded when the step was applied
        timestamp = entry.get("timestamp", "Not recorded")
        lines.append(f"  Timestamp  : {timestamp}")

        # Affected columns — may be an empty list for whole-dataset operations
        columns = entry.get("columns", [])
        if columns:
            lines.append(f"  Columns    : {', '.join(str(c) for c in columns)}")
        else:
            lines.append("  Columns    : All columns (or not applicable)")

        # Parameters — may be a dict, a list, None, or missing entirely
        parameters = entry.get("parameters", None)

        if parameters is None:
            lines.append("  Parameters : None recorded")

        elif isinstance(parameters, dict):
            if parameters:
                lines.append("  Parameters :")
                for key, value in parameters.items():
                    lines.append(f"    - {key}: {value}")
            else:
                lines.append("  Parameters : None recorded")

        elif isinstance(parameters, list):
            if parameters:
                lines.append("  Parameters :")
                for item in parameters:
                    lines.append(f"    - {item}")
            else:
                lines.append("  Parameters : None recorded")

        else:
            # Fallback — covers any other unexpected type
            lines.append(f"  Parameters : {parameters}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("  END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)