# ✅ TEST CHECKLIST
## AI-Assisted Data Wrangler & Visualizer

Use this checklist to manually test the app before your demo or submission.
Tick each item as you verify it works correctly.

---

## 1. General App Launch & Navigation

- [✅] App launches without errors using `streamlit run app.py`
- [✅] Main page shows title, welcome message, and info box
- [✅] Help / usage guide section is visible on the main page
- [✅] Quick Navigation section is visible with all 4 page descriptions
- [✅] Sidebar shows app navigation with all 4 pages listed
- [✅] All 4 pages appear in the sidebar and can be clicked
- [✅] Sidebar shows Reset Session button at all times
- [✅] Sidebar shows Reset to Original Data button after data is loaded
- [✅] Sidebar shows Undo Last Action button (greyed out when no undo available)
- [✅] Sidebar shows Last Action summary after a transformation is applied
- [✅] Navigating between pages does not crash the app

---

## 2. Upload & Overview Page

### File Upload
- [✅] File uploader widget is visible
- [✅] CSV file uploads and loads correctly
- [✅] XLSX file uploads and loads correctly
- [✅] JSON file uploads and loads correctly
- [✅] Unsupported file type (e.g. `.txt`) shows a friendly error message
- [✅] Empty file shows a friendly error message
- [✅] Success message appears after successful upload

### Dataset Persistence
- [✅] Navigating away and returning to Upload page still shows data
- [✅] Info message appears saying dataset is already loaded
- [✅] All overview sections still show after returning to the page

### Current Dataset Summary Box
- [✅] Shows file name, rows, columns, numeric count, categorical count, transformations

### Overview Sections
- [✅] File Information section shows name, type, shape
- [✅] Data Preview shows first 5 rows correctly
- [✅] Column & Data Type Summary shows all columns with correct dtypes
- [✅] Missing Values Summary shows affected columns or success message
- [✅] Duplicate Rows section shows count or success message
- [✅] Numeric Summary shows descriptive stats for numeric columns
- [✅] Categorical Summary shows unique count and most frequent values

---

## 3. Cleaning & Preparation Page

### Page Guards
- [✅] Warning and stop shown if no data is loaded
- [✅] Page loads correctly after data is uploaded

### Current Data Summary Box
- [✅] Shows file name, rows, columns, numeric count, categorical count, transformations

### Navigation Bar
- [✅] Jump-to-section links visible near top of page
- [✅] Clicking a link scrolls to the correct section

### Missing Values
- [✅] Missing Values Analysis table shows correctly
- [✅] Fill Missing Values with Constant fills correctly and updates log
- [✅] Fill with numeric value works on numeric columns
- [✅] Fill with text value works on text columns
- [✅] Drop Rows with Missing Values removes correct rows and updates log
- [✅] Both actions show updated shape after applying

### Duplicates
- [✅] Duplicate Rows Analysis shows correct count and preview
- [✅] Remove Full-Row Duplicates removes correct rows with keep=first
- [✅] Remove Full-Row Duplicates removes correct rows with keep=last
- [✅] Remove Duplicates by Columns removes rows based on selected columns
- [✅] Both actions update shape and log

### Data Type Conversion
- [✅] Data Type Overview table shows all columns and current types
- [✅] Convert to string works correctly
- [✅] Convert to category works correctly
- [✅] Convert to numeric works (non-convertible become NaN)
- [✅] Convert to datetime works (non-convertible become NaT)

### Text Cleaning
- [✅] Standardize Text Case — lower works correctly
- [✅] Standardize Text Case — title works correctly
- [✅] NaN values are not turned into the string "nan"
- [✅] Replace Values replaces exact matches correctly
- [✅] Replace Values leaves unselected columns unchanged

### Category Tools
- [✅] Group Rare Categories shows current value counts for selected column
- [✅] Values below threshold are replaced with "Other"
- [✅] Missing values are not affected by grouping

### Outlier Tools
- [✅] Outlier Analysis shows Q1, Q3, IQR, bounds, and count correctly
- [✅] Outlier rows preview appears when outliers exist
- [✅] Remove Outlier Rows removes correct rows and updates shape and log

### Scaling
- [✅] Min-Max Scaling scales values to 0–1 range
- [✅] Z-Score Standardization scales to mean=0, std=1
- [✅] Columns with all-identical values are left unchanged safely

### Column Operations
- [✅] Rename Column renames correctly and updates log
- [✅] Rename to existing name shows validation error
- [✅] Rename to same name shows info message
- [✅] Drop Columns removes selected columns and updates log

### Validation Rules
- [✅] Check Allowed Values shows success when all values are valid
- [✅] Check Allowed Values shows warning and preview when invalid values found
- [✅] Empty allowed values input shows error
- [✅] Check Datetime Parse Readiness shows metrics and failed rows correctly
- [✅] Validation checks do not modify working_df

### Transformation Log
- [✅] Log entries appear in order after each transformation
- [✅] Each entry shows operation, timestamp, columns, parameters
- [✅] Clear Transformation Log button clears log and shows success

### Current Data Preview
- [✅] Preview shows correct rows after transformations
- [✅] Row count selector works (5, 10, 20, 50)

### Undo / Reset (from sidebar)
- [✅] Undo Last Action restores previous working_df
- [✅] Undo is greyed out when no undo state is available
- [✅] Reset to Original Data restores original uploaded dataset
- [✅] Reset does not affect transformation_log removal (log entry is added)

---

## 4. Visualization Builder Page

### Page Guards
- [✅] Warning and stop shown if no data is loaded
- [✅] Page loads correctly after data is uploaded

### Current Data Summary Box
- [✅] Shows file name, rows, columns, numeric count, categorical count, transformations

### Dataset Info & Preview
- [✅] Dataset info metrics show correctly
- [✅] Data Preview shows top 10 rows

### Column Summary
- [✅] Numeric and categorical column counts are correct

### Chart Builder Controls
- [✅] Chart Type selectbox shows all 6 options
- [✅] Reset Chart Controls button resets all chart widget selections

### Current Chart Settings Panel
- [✅] Expander shows current chart type, color, size, labels
- [✅] Column selections update correctly per chart type

### Chart Customization
- [✅] Figure width and height sliders work
- [✅] Color selectbox changes chart color
- [✅] Custom chart title is applied when entered
- [✅] Custom X/Y axis labels are applied when entered
- [✅] Defaults are used when fields are left empty

### Histogram
- [✅] Generates correctly for a numeric column
- [✅] Bin slider changes number of bins
- [✅] Warning shown if no numeric columns exist
- [✅] Warning shown if column has no non-missing values

### Bar Chart
- [✅] Generates correctly for a categorical column
- [✅] X labels rotate when many categories exist
- [✅] Warning shown if no categorical columns exist

### Line Chart
- [✅] Generates correctly for X and Y column selection
- [✅] Missing values are dropped safely before plotting
- [✅] Warning shown if no numeric columns exist

### Scatter Plot
- [✅] Generates correctly for two numeric columns
- [✅] Warning shown if fewer than 2 numeric columns exist

### Box Plot
- [✅] Generates correctly for a numeric column
- [✅] Warning shown if no numeric columns exist

### Pie Chart
- [✅] Generates correctly for a categorical column
- [✅] Percentages shown on slices
- [✅] Warning shown if no categorical columns exist

### Chart Download
- [✅] Download Chart as PNG button appears after chart is generated
- [✅] Downloaded PNG file opens correctly and matches rendered chart

---

## 5. Export & Report Page

### Page Guards
- [✅] Warning and stop shown if no data is loaded
- [✅] Page loads correctly after data is uploaded

### Export Summary Box
- [✅] Shows file name, rows, columns, logged transformations
- [✅] Shows available export formats

### Reset Export View
- [✅] Reset Export View button runs without error

### Transformation Log Summary
- [✅] Log entries display correctly in expanders
- [✅] Empty log shows info message

### Data Preview
- [✅] Top 10 rows of working_df shown correctly

### CSV Export
- [✅] Download Cleaned Data as CSV button appears
- [✅] Downloaded file opens correctly in Excel or a text editor
- [✅] Filename is based on original uploaded file name

### Excel Export
- [✅] Download Cleaned Data as Excel button appears
- [✅] Downloaded .xlsx file opens correctly
- [✅] Filename is based on original uploaded file name

### JSON Export
- [✅] Download Cleaned Data as JSON button appears
- [✅] Downloaded JSON file is valid and readable
- [✅] Filename is based on original uploaded file name

### TXT Report Download
- [✅] Download Transformation Report button appears
- [✅] Downloaded .txt file contains app name, file name, shape, and log entries
- [✅] Empty log produces a report saying no transformations recorded

### Report Preview
- [✅] On-page report preview renders correctly
- [✅] Preview matches what would be downloaded

---

## 6. Reset / Undo Behavior

- [✅] Undo Last Action restores exactly one step back
- [✅] After undo, undo button becomes greyed out (only one step supported)
- [✅] Reset to Original Data restores full original dataset
- [✅] Reset to Original Data clears undo stack
- [✅] Reset Session (sidebar) clears everything including data, log, and undo
- [✅] After Reset Session, app behaves as if freshly opened
- [✅] None of the reset/undo actions affect original_df directly

---

## 7. Edge Cases / Invalid Inputs

- [✅] Uploading a second file replaces the first correctly
- [✅] Applying fill with empty fill value shows error, does not crash
- [✅] Applying drop rows with no columns selected shows error
- [✅] Applying type conversion with no columns selected shows error
- [✅] Rename column to an already-used name shows error
- [✅] Outlier removal on a column with no outliers shows info, does not crash
- [✅] Min-Max scaling on a constant column (all same value) does not crash
- [✅] Z-score scaling on a constant column does not crash
- [✅] Histogram on a column with all missing values shows warning, does not crash
- [✅] Scatter plot with fewer than 2 numeric columns shows warning
- [✅] Check Allowed Values with empty input shows error
- [✅] Datetime parse check on a column with all missing values shows info
- [✅] Navigating to Cleaning page before uploading shows warning and stops safely
- [✅] Navigating to Visualization page before uploading shows warning and stops safely
- [✅] Navigating to Export page before uploading shows warning and stops safely

---

## 8. Final Demo Readiness

- [✅] App launches cleanly with no console errors on startup
- [✅] All 4 pages load without errors
- [✅] A full workflow runs end-to-end:
  - [✅] Upload a CSV dataset
  - [✅] Review the overview
  - [✅] Apply at least 3 cleaning actions
  - [✅] Build at least 2 different chart types
  - [✅] Export cleaned data as CSV
  - [✅] Download transformation report as TXT
- [✅] Transformation log records all applied actions correctly
- [✅] Sidebar controls work from every page
- [✅] App handles a dataset with missing values and duplicates correctly
- [✅] App handles a clean dataset without crashing or showing false warnings
- [✅] All download buttons produce valid, non-empty files
- [✅] Page titles, descriptions, and section headers are clean and consistent
- [✅] No placeholder "under development" messages remain in active sections

---

*Checklist version: Final pre-submission*
*Project: AI-Assisted Data Wrangler & Visualizer*