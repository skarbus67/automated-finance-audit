import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DB_DIR = BASE_DIR / "database"

HR_EXCEL_PATH = RAW_DATA_DIR / "hr_employee_directory.xlsx"
SAP_CSV_PATH = RAW_DATA_DIR / "sap_expenses_extract.csv"
SCHEMA_SQL_PATH = DB_DIR / "schema.sql"
DB_PATH = DB_DIR / "reconciliation.db"

EXCHANGE_RATES = {
    "PLN": 1.00,
    "EUR": 4.30,
    "USD": 4.00,
}


def parse_amount(val: object) -> Optional[float]:
    """Convert a messy string amount (with spaces and commas) to a float."""
    if pd.isna(val):
        return None
    cleaned = str(val).strip().replace(" ", "").replace(",", ".")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(val: object) -> Optional[str]:
    """Standardize various date formats into ISO format (YYYY-MM-DD)."""
    if pd.isna(val):
        return None
    cleaned = str(val).strip()
    if not cleaned:
        return None

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def extract_and_clean_hr_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and clean HR data from the Excel workbook."""
    df_emp = pd.read_excel(HR_EXCEL_PATH, sheet_name="Employees", dtype=str)
    df_cc = pd.read_excel(HR_EXCEL_PATH, sheet_name="Cost_Centers", dtype=str)

    df_cc["cost_center_id"] = df_cc["cost_center_id"].str.strip().str.upper()
    df_cc["department_name"] = df_cc["department_name"].str.strip()
    df_cc["manager_email"] = df_cc["manager_email"].str.strip().str.lower()
    df_cc["total_budget_pln"] = df_cc["total_department_budget_pln"].apply(parse_amount)

    df_cc_clean = df_cc[
        ["cost_center_id", "department_name", "manager_email", "total_budget_pln"]
    ].copy()

    df_emp["emp_id"] = df_emp["emp_id"].str.strip().str.upper()
    df_emp["full_name"] = df_emp["full_name"].str.strip()
    df_emp["cost_center_id"] = df_emp["cost_center_id"].str.strip().str.upper()
    df_emp["monthly_limit_pln"] = df_emp["monthly_limit_pln"].apply(parse_amount)
    df_emp["status"] = df_emp["status"].str.strip().str.capitalize()
    df_emp["termination_date"] = df_emp["termination_date"].apply(
        lambda x: parse_date(x) if pd.notna(x) and str(x).strip().lower() != "none" else None
    )

    df_emp_clean = df_emp[
        [
            "emp_id",
            "full_name",
            "cost_center_id",
            "monthly_limit_pln",
            "status",
            "termination_date",
        ]
    ].copy()

    return df_cc_clean, df_emp_clean


def extract_and_clean_sap_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, clean, and validate SAP CSV expenses, separating valid and rejected rows."""
    df_raw = pd.read_csv(
        SAP_CSV_PATH,
        dtype=str,
        keep_default_na=False,
        skip_blank_lines=True,
    )

    df_raw = df_raw[
        df_raw.apply(lambda r: any(str(val).strip() != "" for val in r), axis=1)
    ].copy()

    valid_rows = []
    rejected_rows = []
    seen_tx_ids = set()

    for _, row in df_raw.iterrows():
        raw_tx_id = str(row.get("tx_id", "")).strip().upper()
        raw_emp_id = str(row.get("emp_id", "")).strip().upper()
        raw_cc_id = str(row.get("cost_center_id", "")).strip().upper()
        raw_date = str(row.get("tx_date", "")).strip()
        raw_amount = str(row.get("amount", "")).strip()
        raw_curr = str(row.get("currency", "")).strip().upper()
        vendor = str(row.get("vendor", "")).strip()
        description = str(row.get("description", "")).strip()

        reasons = []

        if not raw_tx_id:
            reasons.append("Missing tx_id")
        elif raw_tx_id in seen_tx_ids:
            reasons.append("Technical duplicate tx_id")

        if not raw_emp_id:
            reasons.append("Missing emp_id")

        if not raw_cc_id:
            reasons.append("Missing cost_center_id")

        iso_date = parse_date(raw_date)
        if not iso_date:
            reasons.append("Invalid or missing tx_date")

        parsed_amount = parse_amount(raw_amount)
        if parsed_amount is None:
            reasons.append("Unparseable amount")
        elif parsed_amount <= 0:
            reasons.append("Negative or zero amount")

        if raw_curr not in EXCHANGE_RATES:
            reasons.append(f"Unsupported currency: {raw_curr}")

        if reasons:
            rejected_rows.append(
                {
                    "raw_tx_id": raw_tx_id,
                    "raw_emp_id": raw_emp_id,
                    "raw_cost_center_id": raw_cc_id,
                    "raw_tx_date": raw_date,
                    "raw_amount": raw_amount,
                    "raw_currency": raw_curr,
                    "vendor": vendor,
                    "description": description,
                    "rejection_reason": "; ".join(reasons),
                }
            )
        else:
            seen_tx_ids.add(raw_tx_id)
            amount_pln = round(parsed_amount * EXCHANGE_RATES[raw_curr], 2)
            valid_rows.append(
                {
                    "tx_id": raw_tx_id,
                    "emp_id": raw_emp_id,
                    "cost_center_id": raw_cc_id,
                    "tx_date": iso_date,
                    "original_amount": parsed_amount,
                    "original_currency": raw_curr,
                    "amount_pln": amount_pln,
                    "vendor": vendor,
                    "description": description,
                }
            )

    df_valid = pd.DataFrame(valid_rows)
    df_rejected = pd.DataFrame(rejected_rows)
    return df_valid, df_rejected


def load_to_database(
    df_cc: pd.DataFrame,
    df_emp: pd.DataFrame,
    df_sap: pd.DataFrame,
    df_rejected: pd.DataFrame,
) -> None:
    """Initialize SQLite schema and load cleaned DataFrames into reconciliation.db."""
    DB_DIR.mkdir(parents=True, exist_ok=True)

    with open(SCHEMA_SQL_PATH, "r", encoding="utf-8") as schema_file:
        schema_sql = schema_file.read()

    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(schema_sql)

        df_cc.to_sql("cost_centers", conn, if_exists="append", index=False)
        df_emp.to_sql("employees", conn, if_exists="append", index=False)
        df_sap.to_sql("sap_transactions", conn, if_exists="append", index=False)
        df_rejected.to_sql("rejected_rows", conn, if_exists="append", index=False)


def main() -> None:
    print("--- Starting ETL & Data Cleaning (Module 3) ---")
    df_cc, df_emp = extract_and_clean_hr_data()
    print(f"[OK] Cleaned HR data: {len(df_emp)} employees, {len(df_cc)} cost centers.")

    df_sap_valid, df_sap_rejected = extract_and_clean_sap_data()
    print(f"[OK] Processed SAP transactions: {len(df_sap_valid)} valid, {len(df_sap_rejected)} rejected.")

    load_to_database(df_cc, df_emp, df_sap_valid, df_sap_rejected)
    print(f"[OK] Loaded all tables into SQLite database: {DB_PATH}")
    print("--- ETL Process Completed Successfully ---")


if __name__ == "__main__":
    main()