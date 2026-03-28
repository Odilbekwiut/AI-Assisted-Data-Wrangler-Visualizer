# Prompts Used During Development

## Purpose
This file provides a clean summary of the main prompts used during the development of the Streamlit coursework project **AI-Assisted Data Wrangler & Visualizer**.

It is intended to document the major AI prompts used across planning, building, debugging, and final submission preparation.

## Core prompt style used throughout the project

A repeated prompt pattern used during development was:

- continue the same Streamlit coursework app
- work in PATCH MODE
- do not rewrite whole files
- preserve architecture and existing behavior
- add or fix one small required feature
- return exact code and where to paste it

This pattern was used because the project was developed gradually and stability was important near the deadline.

---

## Main prompt categories

### 1. Coursework understanding and planning
Examples of prompts used:
- Read the coursework files and explain what the app must include
- Break the project into small step-by-step tasks
- Tell us which features are required and which are optional
- Help us continue in small sequential steps
- Create a transition prompt so we can move to a new chat without losing progress

**Purpose:**  
To understand the brief and organize the work clearly.

---

### 2. App structure and page design
Examples of prompts used:
- Help us structure the app into the required Streamlit pages
- Keep the app beginner-friendly and aligned with the coursework workflow
- Preserve the current architecture and patch only what is necessary

**Purpose:**  
To build the app around a clear multi-page workflow.

---

### 3. Data cleaning and preparation features
Examples of prompts used:
- Help us add missing value handling
- Help us implement duplicate removal
- Add data type conversion/parsing tools
- Add categorical cleaning and numeric cleaning features
- Add column operations and preparation tools
- Keep old working behavior while adding new features

**Purpose:**  
To implement the main data wrangling requirements.

---

### 4. Visualization features
Examples of prompts used:
- Help us build matplotlib charts for the visualization page
- Preserve existing summaries, preview behavior, and download behavior
- Add one feature without breaking the current visualization page

**Purpose:**  
To implement the data visualization requirements.

---

### 5. Export and reporting
Examples of prompts used:
- Add export options for CSV, Excel, JSON
- Add transformation report preview and TXT download
- Patch the transformation report so it includes required information
- Add workflow reproducibility using JSON export

**Purpose:**  
To complete the reporting and export requirements.

---

### 6. Session state and transformation logging
Examples of prompts used:
- Diagnose why transformations are not appearing in the report
- Check whether `transformation_log` is being reset
- Log transformations only after successful dataframe updates
- Keep the log structure consistent across pages

**Purpose:**  
To make the app workflow traceable and reproducible.

---

### 7. Debugging and patching
Examples of prompts used:
- Continue from the exact current point
- Diagnose this specific error and patch only the necessary part
- Do not rewrite the app
- Return exact code and tell us where to paste it

**Purpose:**  
To fix problems safely without destabilizing working features.

---

### 8. Deployment and final updates
Examples of prompts used:
- Tell us how to push the updated code to GitHub
- Help us make the Streamlit online app reflect the newest version
- Tell us what is still left based on the coursework brief

**Purpose:**  
To keep the local and deployed versions aligned and identify final remaining tasks.

---

### 9. Submission preparation
Examples of prompts used:
- Help us understand which files must be submitted
- Tell us what to keep or remove from the ZIP
- Help us prepare AI documentation files
- Help us organize deliverables according to the brief

**Purpose:**  
To prepare the final coursework submission correctly.

## Final note
This file summarizes the main prompts used across the project. It is intended to document the actual AI-assisted workflow used during development in a clear and organized form, rather than list every small message individually.