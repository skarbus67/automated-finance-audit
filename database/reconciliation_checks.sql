SELECT
    c.cost_center_id,
    c.department_name,
    c.manager_email,
    c.total_budget_pln,
    COUNT(t.tx_id) AS total_transactions,
    ROUND(COALESCE(SUM(t.amount_pln), 0), 2) AS actual_spend_pln,
    ROUND(c.total_budget_pln - COALESCE(SUM(t.amount_pln), 0), 2) AS remaining_budget_pln,
    ROUND((COALESCE(SUM(t.amount_pln), 0) / c.total_budget_pln) * 100, 2) AS budget_utilization_pct
FROM cost_centers c
LEFT JOIN sap_transactions t ON c.cost_center_id = t.cost_center_id
GROUP BY c.cost_center_id, c.department_name, c.manager_email, c.total_budget_pln
ORDER BY budget_utilization_pct DESC;

SELECT
    e.emp_id,
    e.full_name,
    e.cost_center_id,
    c.department_name,
    e.status,
    COUNT(t.tx_id) AS tx_count,
    e.monthly_limit_pln,
    ROUND(SUM(t.amount_pln), 2) AS total_spent_pln,
    ROUND(SUM(t.amount_pln) - e.monthly_limit_pln, 2) AS overrun_amount_pln,
    ROUND((SUM(t.amount_pln) / e.monthly_limit_pln) * 100, 2) AS limit_utilization_pct
FROM sap_transactions t
INNER JOIN employees e ON t.emp_id = e.emp_id
LEFT JOIN cost_centers c ON e.cost_center_id = c.cost_center_id
GROUP BY e.emp_id, e.full_name, e.cost_center_id, c.department_name, e.status, e.monthly_limit_pln
HAVING SUM(t.amount_pln) > e.monthly_limit_pln
ORDER BY overrun_amount_pln DESC;


SELECT
    t.tx_id,
    t.emp_id,
    e.full_name,
    e.status,
    e.termination_date,
    t.tx_date,
    CAST(julianday(t.tx_date) - julianday(e.termination_date) AS INTEGER) AS days_after_termination,
    t.cost_center_id,
    t.vendor,
    t.description,
    t.original_amount,
    t.original_currency,
    t.amount_pln
FROM sap_transactions t
INNER JOIN employees e ON t.emp_id = e.emp_id
WHERE e.status = 'Terminated'
  AND t.tx_date > e.termination_date
ORDER BY t.tx_date DESC;


WITH DuplicateCheck AS (
    SELECT
        t.tx_id,
        t.emp_id,
        e.full_name,
        t.cost_center_id,
        t.tx_date,
        t.vendor,
        t.description,
        t.original_amount,
        t.original_currency,
        t.amount_pln,
        COUNT(*) OVER (
            PARTITION BY t.emp_id, t.tx_date, t.original_amount, t.vendor
        ) AS duplicate_count
    FROM sap_transactions t
    LEFT JOIN employees e ON t.emp_id = e.emp_id
)
SELECT
    tx_id,
    emp_id,
    full_name,
    cost_center_id,
    tx_date,
    vendor,
    description,
    original_amount,
    original_currency,
    amount_pln,
    duplicate_count
FROM DuplicateCheck
WHERE duplicate_count > 1
ORDER BY tx_date, emp_id, tx_id;


SELECT
    t.tx_id,
    t.emp_id,
    e.full_name,
    t.tx_date,
    t.cost_center_id AS sap_cost_center_id,
    e.cost_center_id AS hr_cost_center_id,
    c.department_name AS sap_cc_department,
    t.vendor,
    t.description,
    t.amount_pln,
    CASE
        WHEN c.cost_center_id IS NULL THEN 'Invalid Cost Center (Not in Dictionary)'
        WHEN t.cost_center_id != e.cost_center_id THEN 'Employee Cost Center Mismatch'
        ELSE 'Other Anomaly'
    END AS mismatch_reason
FROM sap_transactions t
LEFT JOIN employees e ON t.emp_id = e.emp_id
LEFT JOIN cost_centers c ON t.cost_center_id = c.cost_center_id
WHERE c.cost_center_id IS NULL
   OR t.cost_center_id != e.cost_center_id
ORDER BY t.tx_date DESC;


SELECT
    raw_tx_id,
    raw_emp_id,
    raw_cost_center_id,
    raw_tx_date,
    raw_amount,
    raw_currency,
    vendor,
    description,
    rejection_reason
FROM rejected_rows;