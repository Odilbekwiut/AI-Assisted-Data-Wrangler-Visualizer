import streamlit as st
import matplotlib.pyplot as plt
import io

def get_chart_download_button(fig, filename):
    """
    Saves a matplotlib figure to an in-memory buffer and returns
    a Streamlit download button for it as a PNG file.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    st.download_button(
        label="⬇ Download Chart as PNG",
        data=buf,
        file_name=filename,
        mime="image/png",
        key=f"download_{filename}"
    )

from utils.session_state import initialize_session_state, data_is_loaded, render_sidebar_controls

# Always initialize session state at the top of every page
initialize_session_state()
render_sidebar_controls()

# --- Page Title and Description ---
st.title("Visualization Builder")

st.write(
    "Build charts from your cleaned dataset. "
    "Choose a chart type, select your columns, and explore your data visually. "
    "All charts are built using matplotlib."
)

# --- Current Data Summary ---
if data_is_loaded():
    _df = st.session_state.working_df
    _numeric = _df.select_dtypes(include=["number"]).shape[1]
    _categorical = _df.select_dtypes(include=["object", "category"]).shape[1]

    with st.container():
        st.markdown("### 📊 Current Data Summary")

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

# ---- Dataset Info ----
st.subheader("Dataset Info")

col1, col2, col3 = st.columns(3)
col1.metric("File", st.session_state.uploaded_file_name)
col2.metric("Rows", df.shape[0])
col3.metric("Columns", df.shape[1])

st.divider()

# ---- Data Preview ----
st.subheader("Data Preview (Top 10 Rows)")
st.dataframe(df.head(10), use_container_width=True)

st.divider()

# ---- Column Summary ----
# Identify numeric and categorical columns
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
all_cols = df.columns.tolist()

st.subheader("Column Summary")

col1, col2 = st.columns(2)
col1.info(f"**Numeric columns:** {len(numeric_cols)}")
col2.info(f"**Categorical columns:** {len(categorical_cols)}")

st.divider()
st.subheader("Chart Customization")
st.write("Adjust size, color, and labels for your chart.")

# --- Figure Size Controls ---
st.write("**Figure Size**")
size_col1, size_col2 = st.columns(2)

with size_col1:
    fig_width = st.slider(
        label="Width",
        min_value=4,
        max_value=20,
        value=8,
        step=1,
        key="fig_width"
    )

with size_col2:
    fig_height = st.slider(
        label="Height",
        min_value=3,
        max_value=15,
        value=5,
        step=1,
        key="fig_height"
    )

# --- Color Control ---
st.write("**Chart Color**")
chart_color = st.selectbox(
    label="Select a chart color",
    options=[
        "steelblue", "tomato", "seagreen", "mediumpurple",
        "darkorange", "goldenrod", "slategray", "crimson"
    ],
    key="chart_color"
)

# --- Optional Chart Customization ---
st.write("**Optional: Customize chart labels**")

custom_title = st.text_input(
    label="Chart title (leave blank for default)",
    placeholder="e.g. Sales by Region",
    key="custom_title"
)

custom_xlabel = st.text_input(
    label="X-axis label (leave blank for default)",
    placeholder="e.g. Month",
    key="custom_xlabel"
)

custom_ylabel = st.text_input(
    label="Y-axis label (leave blank for default)",
    placeholder="e.g. Total Sales",
    key="custom_ylabel"
)

st.divider()

# ---- Chart Builder Controls ----
st.subheader("Chart Builder Controls")

st.write(
    "Select a chart type and the columns you want to visualize. "
    "Chart output will appear below once generation is added."
)

# --- Reset Chart Controls ---
if st.button("🔄 Reset Chart Controls", key="btn_reset_chart_controls"):
    # Clear only visualization-related session state keys
    chart_keys = [
        "chart_type", "chart_x_axis", "chart_y_axis",
        "hist_column", "hist_bins",
        "bar_column",
        "line_x", "line_y",
        "scatter_x", "scatter_y",
        "box_column",
        "pie_column",
        "fig_width", "fig_height",
        "chart_color",
        "custom_title", "custom_xlabel", "custom_ylabel"
    ]
    for key in chart_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.rerun()

chart_type = st.selectbox(
    label="Chart Type",
    options=["Histogram", "Bar Chart", "Line Chart", "Scatter Plot", "Box Plot", "Pie Chart"],
    key="chart_type"
)

x_axis = st.selectbox(
    label="X-Axis Column",
    options=all_cols,
    key="chart_x_axis"
)

y_axis = st.selectbox(
    label="Y-Axis Column (not needed for all chart types)",
    options=["None"] + all_cols,
    key="chart_y_axis"
)

# ---- Current Chart Settings Summary ----
with st.expander("📋 Current Chart Settings", expanded=False):

    st.write(f"**Chart Type:** {chart_type}")
    st.write(f"**Color:** {chart_color}")
    st.write(f"**Figure Size:** {fig_width} × {fig_height}")
    st.write(f"**Chart Title:** {custom_title if custom_title.strip() else '(default)'}")

    # X and Y labels — relevant for all except pie
    if chart_type != "Pie Chart":
        st.write(f"**X-Axis Label:** {custom_xlabel if custom_xlabel.strip() else '(default)'}")
        st.write(f"**Y-Axis Label:** {custom_ylabel if custom_ylabel.strip() else '(default)'}")

    # Show column selections based on chart type
    if chart_type == "Histogram":
        st.write(f"**Column:** {st.session_state.get('hist_column', '(not selected yet)')}")

    elif chart_type == "Bar Chart":
        st.write(f"**Column:** {st.session_state.get('bar_column', '(not selected yet)')}")

    elif chart_type == "Line Chart":
        st.write(f"**X Column:** {st.session_state.get('line_x', '(not selected yet)')}")
        st.write(f"**Y Column:** {st.session_state.get('line_y', '(not selected yet)')}")

    elif chart_type == "Scatter Plot":
        st.write(f"**X Column:** {st.session_state.get('scatter_x', '(not selected yet)')}")
        st.write(f"**Y Column:** {st.session_state.get('scatter_y', '(not selected yet)')}")

    elif chart_type == "Box Plot":
        st.write(f"**Column:** {st.session_state.get('box_column', '(not selected yet)')}")

    elif chart_type == "Pie Chart":
        st.write(f"**Column:** {st.session_state.get('pie_column', '(not selected yet)')}")

st.divider()

# ---- Chart Output ----
st.subheader("Chart Output")

# --- Pre-flight column availability check ---
# Before rendering any chart controls, verify required columns exist.
# This prevents blank or confusing behavior when datasets lack certain column types.

_chart_blocked = False

if chart_type == "Histogram":
    if not numeric_cols:
        st.warning("Histogram requires at least one numeric column. None found in the current dataset.")
        _chart_blocked = True

elif chart_type == "Bar Chart":
    if not categorical_cols:
        st.warning("Bar Chart requires at least one categorical column. None found in the current dataset.")
        _chart_blocked = True

elif chart_type == "Line Chart":
    if not numeric_cols:
        st.warning("Line Chart requires at least one numeric column for the Y-axis. None found in the current dataset.")
        _chart_blocked = True

elif chart_type == "Scatter Plot":
    if len(numeric_cols) < 2:
        st.warning("Scatter Plot requires at least two numeric columns. Not enough found in the current dataset.")
        _chart_blocked = True

elif chart_type == "Box Plot":
    if not numeric_cols:
        st.warning("Box Plot requires at least one numeric column. None found in the current dataset.")
        _chart_blocked = True

elif chart_type == "Pie Chart":
    if not categorical_cols:
        st.warning("Pie Chart requires at least one categorical column. None found in the current dataset.")
        _chart_blocked = True

if _chart_blocked:
    st.stop()
    
#-----Chart rendering logic is below, but it will only run if the pre-flight checks above are passed

if chart_type == "Histogram":

    st.write("Configure your histogram below.")

    # Only numeric columns are valid for a histogram
    if not numeric_cols:
        st.warning("No numeric columns found in the current dataset.")

    else:
        hist_column = st.selectbox(
            label="Select a numeric column",
            options=numeric_cols,
            key="hist_column"
        )

        hist_bins = st.slider(
            label="Number of bins",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            key="hist_bins"
        )

        if st.button("Generate Histogram", key="btn_histogram"):

            # Drop missing values before plotting so matplotlib doesn't crash
            plot_data = df[hist_column].dropna()

            if plot_data.empty:
                st.warning(
                    f"The column `{hist_column}` has no non-missing values to plot."
                )

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.hist(plot_data, bins=hist_bins, edgecolor="black", color=chart_color)

                ax.set_title(custom_title if custom_title.strip() else f"Histogram of {hist_column}")
                ax.set_xlabel(custom_xlabel if custom_xlabel.strip() else hist_column)
                ax.set_ylabel(custom_ylabel if custom_ylabel.strip() else "Frequency")

                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    st.dataframe(
                        plot_data.head(10).rename(hist_column),
                        use_container_width=True
                    )
                get_chart_download_button(fig, "histogram_chart.png")
                plt.close(fig)

elif chart_type == "Bar Chart":

    st.write("Configure your bar chart below.")

    if not categorical_cols:
        st.info("No categorical columns found in the current dataset.")

    else:
        bar_column = st.selectbox(
            label="Select a categorical column",
            options=categorical_cols,
            key="bar_column"
        )

        if st.button("Generate Bar Chart", key="btn_bar"):

            # Compute value counts — drop missing values before counting
            plot_data = df[bar_column].dropna().value_counts()

            if plot_data.empty:
                st.warning(
                    f"The column `{bar_column}` has no non-missing values to plot."
                )

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.bar(
                    plot_data.index.astype(str),
                    plot_data.values,
                    edgecolor="black",
                    color=chart_color
                )

                ax.set_title(custom_title if custom_title.strip() else f"Bar Chart of {bar_column}")
                ax.set_xlabel(custom_xlabel if custom_xlabel.strip() else bar_column)
                ax.set_ylabel(custom_ylabel if custom_ylabel.strip() else "Count")

                # Rotate x labels if there are many categories
                if len(plot_data) > 6:
                    plt.xticks(rotation=45, ha="right")

                plt.tight_layout()
                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    st.dataframe(
                        plot_data.head(10).rename(bar_column),
                        use_container_width=True
                    )
                get_chart_download_button(fig, "bar_chart.png")
                plt.close(fig)

elif chart_type == "Line Chart":

    st.write("Configure your line chart below.")

    if not numeric_cols:
        st.warning("No numeric columns found in the current dataset.")

    else:
        line_x = st.selectbox(
            label="Select X-Axis column",
            options=all_cols,
            key="line_x"
        )

        line_y = st.selectbox(
            label="Select Y-Axis column (must be numeric)",
            options=numeric_cols,
            key="line_y"
        )

        if st.button("Generate Line Chart", key="btn_line"):

            # Drop rows where either the x or y column has a missing value
            plot_data = df[[line_x, line_y]].dropna()

            if plot_data.empty:
                st.warning("No data available to plot after removing missing values.")

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.plot(
                    plot_data[line_x],
                    plot_data[line_y],
                    color=chart_color,
                    linewidth=1.5
                )

                ax.set_title(custom_title if custom_title.strip() else f"Line Chart of {line_y} over {line_x}")
                ax.set_xlabel(custom_xlabel if custom_xlabel.strip() else line_x)
                ax.set_ylabel(custom_ylabel if custom_ylabel.strip() else line_y)

                # Rotate x labels if they are text-based or long
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()

                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    st.dataframe(
                        plot_data[[line_x, line_y]].head(10),
                        use_container_width=True
                    )
                get_chart_download_button(fig, "line_chart.png")
                plt.close(fig)

elif chart_type == "Scatter Plot":

    st.write("Configure your scatter plot below.")

    if len(numeric_cols) < 2:
        st.info("Scatter Plot requires at least two numeric columns. Not enough found in the current dataset.")

    else:
        scatter_x = st.selectbox(
            label="Select X-Axis column (numeric)",
            options=numeric_cols,
            key="scatter_x"
        )

        scatter_y = st.selectbox(
            label="Select Y-Axis column (numeric)",
            options=numeric_cols,
            key="scatter_y"
        )

        if st.button("Generate Scatter Plot", key="btn_scatter"):

            # Drop rows where either column has a missing value
            plot_data = df[[scatter_x, scatter_y]].dropna()

            if plot_data.empty:
                st.warning("No data available to plot after removing missing values.")

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.scatter(
                    plot_data[scatter_x],
                    plot_data[scatter_y],
                    color=chart_color,
                    alpha=0.6,
                    edgecolors="black",
                    linewidths=0.4
                )

                ax.set_title(custom_title if custom_title.strip() else f"Scatter Plot of {scatter_y} vs {scatter_x}")
                ax.set_xlabel(custom_xlabel if custom_xlabel.strip() else scatter_x)
                ax.set_ylabel(custom_ylabel if custom_ylabel.strip() else scatter_y)
                plt.tight_layout()
                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    st.dataframe(
                        plot_data[[scatter_x, scatter_y]].head(10),
                        use_container_width=True
                    )
                get_chart_download_button(fig, "scatter_chart.png")
                plt.close(fig)

elif chart_type == "Box Plot":

    st.write("Configure your box plot below.")

    if not numeric_cols:
        st.warning("No numeric columns found in the current dataset.")

    else:
        box_column = st.selectbox(
            label="Select a numeric column",
            options=numeric_cols,
            key="box_column"
        )

        if st.button("Generate Box Plot", key="btn_box"):

            # Drop missing values before plotting
            plot_data = df[box_column].dropna()

            if plot_data.empty:
                st.warning(
                    f"The column `{box_column}` has no non-missing values to plot."
                )

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.boxplot(
                    plot_data,
                    patch_artist=True,          # fills the box with colour
                    boxprops=dict(facecolor=chart_color, color="black"),
                    medianprops=dict(color="white", linewidth=2),
                    whiskerprops=dict(color="black"),
                    capprops=dict(color="black"),
                    flierprops=dict(marker="o", color="black", alpha=0.4)
                )

                ax.set_title(custom_title if custom_title.strip() else f"Box Plot of {box_column}")
                ax.set_ylabel(custom_ylabel if custom_ylabel.strip() else box_column)

                # Remove the default x tick label and replace with column name
                ax.set_xticks([1])
                ax.set_xticklabels([box_column])

                plt.tight_layout()
                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    st.dataframe(
                        plot_data.head(10).to_frame(name=box_column),
                        use_container_width=True
                    )
                get_chart_download_button(fig, "box_chart.png")
                plt.close(fig)

elif chart_type == "Pie Chart":

    st.write("Configure your pie chart below.")

    if not categorical_cols:
        st.warning("No categorical columns found in the current dataset.")

    else:
        pie_column = st.selectbox(
            label="Select a categorical column",
            options=categorical_cols,
            key="pie_column"
        )

        if st.button("Generate Pie Chart", key="btn_pie"):

            # Compute value counts — drop missing values before counting
            plot_data = df[pie_column].dropna().value_counts()

            if plot_data.empty:
                st.warning(
                    f"The column `{pie_column}` has no non-missing values to plot."
                )

            else:
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))

                ax.pie(
                    plot_data.values,
                    labels=plot_data.index.astype(str),
                    autopct="%1.1f%%",      # show percentage on each slice
                    startangle=90,          # start from top
                    # Pie chart uses a full palette — we tint the first slice with the chosen color
                    # and let matplotlib cycle the rest naturally from Set2
                    colors=[chart_color] + list(plt.cm.Set2.colors)
                )

                ax.set_title(custom_title if custom_title.strip() else f"Pie Chart of {pie_column}")

                plt.tight_layout()
                st.pyplot(fig)
                with st.expander("📋 Chart Data Preview", expanded=False):
                    preview_pie = plot_data.reset_index()
                    preview_pie.columns = [pie_column, "Count"]
                    st.dataframe(preview_pie.head(10), use_container_width=True)
                get_chart_download_button(fig, "pie_chart.png")
                plt.close(fig)

else:
    st.info("Configure your settings above and click Generate to build a chart.")

