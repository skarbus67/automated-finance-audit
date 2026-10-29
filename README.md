# Finance & HR Data Reconciliation Pipeline

An end-to-end automated data pipeline designed to extract, clean, validate, and reconcile corporate expense records from **SAP extracts (`.csv`)** against **HR employee and cost center directories (`.xlsx`)**. 

This project was built specifically to demonstrate the core technical competencies required by the **Automation Team at Fresenius Medical Care**: writing analytical SQL queries, building Python data-processing and automation scripts, designing relational data models, reconciling multi-source business data, and delivering clean, well-documented solutions for Finance and HR stakeholders.

---

## Business Purpose & Role Alignment

In large organizations, data exported from ERP systems (like SAP) and HR directories often contain formatting inconsistencies, missing identifiers, or policy violations that require manual verification. This pipeline automates the entire audit workflow and directly addresses the key responsibilities of the role:

* **Clean, Reconcile & Validate Business Data:** Automatically detects discrepancies between SAP expense extracts and HR master data stored in Excel.
* **Python Automation & ETL Scripting:** Implements a modular Python pipeline handling inconsistent date formats, messy number separators, multi-currency conversion, and automated quarantine of corrupted records.
* **Analytical SQL Queries:** Leverages relational joins (`INNER JOIN`, `LEFT JOIN`), Common Table Expressions (`WITH` / CTEs), window functions (`COUNT(*) OVER (PARTITION BY ...)`), date arithmetic (`julianday`), and conditional logic (`CASE WHEN`) to flag financial and security anomalies.
* **Database & Data Model Design:** Uses a normalized SQLite relational schema enforcing foreign key relationships alongside an isolated audit table for rejected records.
* **Automated Reporting & Documentation:** Generates a styled, multi-sheet Excel workbook (`Finance_Audit_Report.xlsx`) ready for Finance and HR review, accompanied by clear operational documentation.

---

## Project Architecture & Directory Structure

The repository is organized into three modular processing stages orchestrated by a central entry-point script (`main.py`):

```text
├── data/
│   ├── output/
│   │   └── Finance_Audit_Report.xlsx       # Formatted multi-sheet Excel audit report for Finance & HR
│   └── raw/
│       ├── hr_employee_directory.xlsx      # Raw HR master data (Sheets: Employees, Cost_Centers)
│       └── sap_expenses_extract.csv        # Raw SAP expense extract containing technical & business anomalies
├── database/
│   ├── reconciliation.db                   # Local SQLite relational database
│   ├── reconciliation_checks.sql           # Suite of 6 SQL reconciliation and audit queries
│   └── schema.sql                          # Relational database schema (DDL) with foreign keys
├── src/
│   ├── 01_generate_mock_data.py            # Step 1: Deterministic mock data & anomaly generator
│   ├── 02_etl_and_clean.py                 # Step 2: ETL, data standardization, validation & DB loading
│   └── 03_run_checks_and_report.py         # Step 3: SQL audit execution & openpyxl Excel report builder
├── .gitignore                              # Git ignore rules
├── main.py                                 # Master orchestrator script executing Steps 1-3
├── README.md                               # Project documentation
└── requirements.txt                        # Python package dependencies
```

---

## Pipeline Workflow

### Step 1: Mock Data Generation (`src/01_generate_mock_data.py`)
Generates a reproducible dataset (`random.seed(42)`) simulating a corporate MedTech environment:
* **HR Master Directory (`hr_employee_directory.xlsx`):**
  * `Cost_Centers` sheet: 5 corporate departments (e.g., *IT & Cloud Infrastructure*, *Finance & Accounting*, *Medical Equipment R&D*) with assigned manager emails and total budgets in PLN.
  * `Employees` sheet: 25 employees with individual monthly spending limits (`monthly_limit_pln`), department assignments, employment statuses (`Active` vs. `Terminated`), and termination dates.
* **Raw SAP Expense Extract (`sap_expenses_extract.csv`):**
  Generates 240+ expense rows across `PLN`, `EUR`, and `USD`, intentionally injecting both **technical noise** and **business policy violations**:
  * *Formatting Noise:* Mixed date formats (`YYYY-MM-DD`, `DD.MM.YYYY`, `YYYY/MM/DD`), inconsistent number formatting (`1250.50`, `1250,50`, `1 250,50`), random leading/trailing whitespace, mixed casing in IDs, and blank CSV lines.
  * *Corrupted Records:* Missing transaction IDs (`tx_id`), missing employee IDs (`emp_id`), negative expense amounts, and exact technical row duplicates.
  * *Business Anomalies:* Post-termination expenses charged by former employees, monthly limit overruns, duplicate vendor billing on the same day, and cross-department or nonexistent cost center charges (`CC-888`, `CC-999`).

### Step 2: ETL, Data Cleaning & Validation (`src/02_etl_and_clean.py`)
Extracts raw files, standardizes formats, validates data integrity, and loads the SQLite database:
* **Standardization:** Strips whitespace, normalizes IDs (`tx_id`, `emp_id`, `cost_center_id`) to uppercase, parses mixed date strings into ISO 8601 format (`YYYY-MM-DD`), and converts messy numeric strings into Python `float` values.
* **Currency Normalization:** Converts original transaction amounts (`PLN`, `EUR`, `USD`) into base currency (`amount_pln`) using predefined exchange rates (`PLN = 1.00`, `EUR = 4.30`, `USD = 4.00`).
* **Data Validation & Quarantine:** Rather than failing on corrupted rows, the pipeline isolates invalid records into the `rejected_rows` table with explicit diagnostic tags (`Missing tx_id`, `Technical duplicate tx_id`, `Missing emp_id`, `Missing cost_center_id`, `Invalid or missing tx_date`, `Unparseable amount`, `Negative or zero amount`, `Unsupported currency`).

### Step 3: Relational Database Schema (`database/schema.sql`)
Cleaned records are persisted in `database/reconciliation.db` across four tables:
* `cost_centers` – Department master table (`cost_center_id` PK, `department_name`, `manager_email`, `total_budget_pln`).
* `employees` – Employee directory (`emp_id` PK, `full_name`, `cost_center_id` FK, `monthly_limit_pln`, `status`, `termination_date`).
* `sap_transactions` – Validated SAP expense transactions (`tx_id` PK, `emp_id` FK, `cost_center_id` FK, `tx_date`, `original_amount`, `original_currency`, `amount_pln`, `vendor`, `description`).
* `rejected_rows` – Audit log storing raw attributes of rejected records alongside `rejection_reason`.

### Step 4: SQL Reconciliation & Excel Reporting (`src/03_run_checks_and_report.py` & `database/reconciliation_checks.sql`)
Executes 6 SQL audit queries against `reconciliation.db` and exports the results into a formatted multi-sheet Excel report (`data/output/Finance_Audit_Report.xlsx`):

| Excel Worksheet | SQL Query Mapping | Audit Check & SQL Techniques Used |
| :--- | :--- | :--- |
| **`Executive_Summary`** | `EXECUTIVE_SUMMARY` | Department-level budget utilization summary: transaction count, actual spend in PLN, remaining budget, and utilization percentage (`LEFT JOIN`, `COALESCE`, `ROUND`, `GROUP BY`). |
| **`Budget_Overruns`** | `BUDGET_OVERRUNS` | Identifies employees whose cumulative monthly expenses exceed their individual `monthly_limit_pln` (`INNER JOIN`, `GROUP BY`, `HAVING SUM(t.amount_pln) > e.monthly_limit_pln`). |
| **`Security_Alerts`** | `SECURITY_ALERTS` | Flags high-priority compliance risks where transactions occurred *after* an employee's termination date, calculating exact days elapsed via `CAST(julianday(t.tx_date) - julianday(e.termination_date) AS INTEGER)`. |
| **`Duplicate_Suspects`** | `DUPLICATE_SUSPECTS` | Detects suspected duplicate billing (same employee, date, original amount, and vendor under different transaction IDs) using a CTE (`WITH DuplicateCheck AS (...)`) and window function `COUNT(*) OVER (PARTITION BY ...)`. |
| **`Data_Mismatches`** | `COST_CENTER_MISMATCHES` & `REJECTED_ROWS` | Combines two audit tables in a single sheet: (1) transactions charged to a cost center that either does not match the employee's HR department or does not exist in the dictionary (`CASE WHEN`), and (2) the full log of ETL-rejected rows. |

All Excel worksheets are automatically styled using `openpyxl` with corporate navy headers (`#1F4E78`), bold white typography, currency formatting (`#,##0.00 "zł"`), percentage formatting (`0.00"%"`), and auto-adjusted column widths.

---

## Getting Started (How to Run)

### 1. Environment Setup
Clone the repository, create a virtual environment, and install the required dependencies (`pandas` and `openpyxl`):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Complete Pipeline
Execute the master orchestrator script from the project root directory to run all three stages sequentially:

```bash
python main.py
```

**Expected Console Output:**
```text
=================================================================
   FINANCE & HR DATA RECONCILIATION PIPELINE - EXECUTION START   
=================================================================

>>> Step 1/3: Mock Data Generation (01_generate_mock_data.py)
--- Starting Mock Data Generation (Module 1) ---
[OK] Generated HR directory file: .../data/raw/hr_employee_directory.xlsx
[OK] Generated SAP CSV extract: .../data/raw/sap_expenses_extract.csv (total lines: 256)
--- Mock Data Generation Completed Successfully ---

>>> Step 2/3: ETL & Data Cleaning (02_etl_and_clean.py)
--- Starting ETL & Data Cleaning (Module 3) ---
[OK] Cleaned HR data: 25 employees, 5 cost centers.
[OK] Processed SAP transactions: 245 valid, 7 rejected.
[OK] Loaded all tables into SQLite database: .../database/reconciliation.db
--- ETL Process Completed Successfully ---

>>> Step 3/3: SQL Reconciliation & Excel Reporting (03_run_checks_and_report.py)
--- Starting SQL Reconciliation Checks & Reporting (Modules 4 & 5) ---
[OK] Generated audit report: .../data/output/Finance_Audit_Report.xlsx
     - Executive_Summary:  5 departments
     - Budget_Overruns:    6 limit overruns
     - Security_Alerts:    4 post-termination expenses
     - Duplicate_Suspects: 4 suspected duplicate rows
     - Data_Mismatches:    4 CC mismatches + 7 ETL rejected rows
--- Audit Report Generation Completed Successfully ---

=================================================================
   PIPELINE COMPLETED SUCCESSFULLY IN 0.45 SECONDS
=================================================================
```

### 3. Run Individual Modules (Optional)
Each stage of the pipeline can also be executed standalone for testing or debugging:

```bash
python src/01_generate_mock_data.py
python src/02_etl_and_clean.py
python src/03_run_checks_and_report.py
```
