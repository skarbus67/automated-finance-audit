
DROP TABLE IF EXISTS rejected_rows;
DROP TABLE IF EXISTS sap_transactions;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS cost_centers;

CREATE TABLE cost_centers (
    cost_center_id TEXT PRIMARY KEY,
    department_name TEXT NOT NULL,
    manager_email TEXT NOT NULL,
    total_budget_pln REAL NOT NULL
);

CREATE TABLE employees (
    emp_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    cost_center_id TEXT NOT NULL,
    monthly_limit_pln REAL NOT NULL,
    status TEXT NOT NULL,
    termination_date TEXT,
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers (cost_center_id)
);

CREATE TABLE sap_transactions (
    tx_id TEXT PRIMARY KEY,
    emp_id TEXT NOT NULL,
    cost_center_id TEXT NOT NULL,
    tx_date TEXT NOT NULL,
    original_amount REAL NOT NULL,
    original_currency TEXT NOT NULL,
    amount_pln REAL NOT NULL,
    vendor TEXT,
    description TEXT,
    FOREIGN KEY (emp_id) REFERENCES employees (emp_id),
    FOREIGN KEY (cost_center_id) REFERENCES cost_centers (cost_center_id)
);

CREATE TABLE rejected_rows (
    raw_tx_id TEXT,
    raw_emp_id TEXT,
    raw_cost_center_id TEXT,
    raw_tx_date TEXT,
    raw_amount TEXT,
    raw_currency TEXT,
    vendor TEXT,
    description TEXT,
    rejection_reason TEXT NOT NULL
);