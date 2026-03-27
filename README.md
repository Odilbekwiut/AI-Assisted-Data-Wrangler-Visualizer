# AI-Assisted Data Wrangler & Visualizer

A multi-page Streamlit app built for a Data Wrangling and Visualization university coursework project.
The app lets you upload a dataset, clean and prepare it, build charts, and export the results — all through a point-and-click interface with no coding required.

---

## Project Overview

This app provides an end-to-end data wrangling workflow:

1. Upload a CSV, XLSX, or JSON dataset
2. Inspect the data with automatic profiling
3. Clean and transform the data using interactive tools
4. Build charts to explore patterns
5. Export the cleaned data and a transformation report

Every cleaning action is recorded in a transformation log that can be reviewed and exported.

---

## Main Features

### Upload & Overview
- Upload CSV, XLSX, or JSON files
- Automatic profiling: shape, column types, missing values, duplicates, numeric and categorical summaries

### Cleaning & Preparation
- Fill missing values with a constant
- Drop rows with missing values
- Remove full-row or column-based duplicates
- Convert column data types (string, category, numeric, datetime)
- Standardize text case (lower, title)
- Replace values in selected columns
- Group rare categories into "Other"
- Outlier analysis and removal (IQR method)
- Min-Max scaling and Z-score standardization
- Rename and drop columns
- Validation checks: allowed values, datetime parse readiness
- Transformation log with undo and reset support

### Visualization Builder
- 6 chart types: Histogram, Bar Chart, Line Chart, Scatter Plot, Box Plot, Pie Chart
- Chart customization: title, axis labels, color, figure size
- Download any chart as a PNG file

### Export & Report
- Export cleaned data as CSV, Excel (.xlsx), or JSON
- Download a plain text transformation report (.txt)
- On-page report preview

---

## App Structure

```
project/
├── app.py                        # Main entry point
├── pages/
│   ├── 1_Upload_Overview.py
│   ├── 2_Cleaning_Preparation.py
│   ├── 3_Visualization_Builder.py
│   └── 4_Export_Report.py
├── utils/
│   ├── session_state.py          # Session state management
│   ├── file_handlers.py          # File loading (CSV, XLSX, JSON)
│   ├── profiling.py              # Dataset profiling helpers
│   └── transformations.py        # All cleaning/transformation functions
├── tests/
│   └── test_smoke_app.py         # Automated smoke tests
├── TEST_CHECKLIST.md             # Manual testing checklist
└── README.md
```

---

## How to Run Locally

**1. Clone or download the project**

**2. Create and activate a virtual environment (recommended)**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate
```

**3. Install required packages**
```bash
pip install -r requirements.txt
```

**4. Run the app**
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## Required Packages

Create a `requirements.txt` with the following:

```
streamlit
pandas
numpy
matplotlib
openpyxl
pytest
```

Install all at once:
```bash
pip install streamlit pandas numpy matplotlib openpyxl pytest
```

---

## Sample Data

The app works with any tabular dataset in CSV, XLSX, or JSON format.

Good datasets to test with:
- [Titanic dataset](https://www.kaggle.com/datasets/hesh97/titanicdataset-traincsv) — has missing values and mixed types
- [Iris dataset](https://archive.ics.uci.edu/dataset/53/iris) — clean numeric data
- Any exported spreadsheet with a mix of text and number columns

For best results, use a dataset that has:
- At least 5–10 columns
- A mix of numeric and text columns
- Some missing values or duplicates to clean

---

## Outputs & Reports

| Output | Format | How to get it |
|---|---|---|
| Cleaned dataset | CSV | Export & Report page |
| Cleaned dataset | Excel (.xlsx) | Export & Report page |
| Cleaned dataset | JSON | Export & Report page |
| Transformation report | TXT | Export & Report page |
| Any chart | PNG | Visualization Builder page |

---

## Testing

### Manual Testing
Use the included checklist to manually verify all features before submission or demo:

```
TEST_CHECKLIST.md
```

The checklist covers all pages, features, edge cases, and export behavior with over 120 checkbox items.

### Automated Smoke Tests
A small pytest smoke test suite is included to verify all pages load without crashing:

```bash
pytest tests/test_smoke_app.py -v
```

Tests cover:
- All 4 pages launching without errors
- No-data warning behavior on protected pages
- Data-loaded behavior using injected session state

---

## Notes on AI Usage

This project was developed with AI assistance (Claude by Anthropic) as part of the coursework learning process.

AI was used to:
- Help plan the app architecture and data flow
- Generate and explain code step by step
- Suggest beginner-friendly patterns for Streamlit, pandas, and matplotlib
- Review and fix bugs during development

All code was reviewed, understood, and integrated manually.
The project structure, feature decisions, and workflow design reflect the coursework requirements and learning objectives.

---

## Project Info

| Field | Detail |
|---|---|
| Course | Data Wrangling and Visualization |
| App name | AI-Assisted Data Wrangler & Visualizer |
| Interface | Streamlit (multi-page) |
| Language | Python 3 |
| Key libraries | pandas, numpy, matplotlib, streamlit |