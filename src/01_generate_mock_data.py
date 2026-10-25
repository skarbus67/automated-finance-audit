import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Set random seed for reproducibility
random.seed(42)

# Define project directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def create_directories() -> None:
    """Create the data/raw directory if it does not exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_hr_data() -> pd.DataFrame:
    """Generate the HR Excel file with Employees and Cost_Centers sheets."""
    cost_centers = [
        {
            "cost_center_id": "CC-100",
            "department_name": "IT & Cloud Infrastructure",
            "manager_email": "m.kowalski@fmc-corp.com",
            "total_department_budget_pln": 45000.00,
        },
        {
            "cost_center_id": "CC-200",
            "department_name": "Finance & Accounting",
            "manager_email": "a.nowak@fmc-corp.com",
            "total_department_budget_pln": 25000.00,
        },
        {
            "cost_center_id": "CC-300",
            "department_name": "Sales & Commercial",
            "manager_email": "p.wisniewski@fmc-corp.com",
            "total_department_budget_pln": 60000.00,
        },
        {
            "cost_center_id": "CC-400",
            "department_name": "HR & Administration",
            "manager_email": "k.wojcik@fmc-corp.com",
            "total_department_budget_pln": 20000.00,
        },
        {
            "cost_center_id": "CC-500",
            "department_name": "Medical Equipment R&D",
            "manager_email": "t.kaminski@fmc-corp.com",
            "total_department_budget_pln": 55000.00,
        },
    ]

    employees = [
        ("EMP001", "Janusz Tracz", "IT & Cloud Infrastructure", "CC-100", 4000, "Active", None),
        ("EMP002", "Anna Lewandowska", "IT & Cloud Infrastructure", "CC-100", 3500, "Active", None),
        ("EMP003", "Piotr Zielinski", "IT & Cloud Infrastructure", "CC-100", 3000, "Active", None),
        ("EMP004", "Katarzyna Mazur", "IT & Cloud Infrastructure", "CC-100", 5000, "Active", None),
        ("EMP005", "Michal Krawczyk", "Finance & Accounting", "CC-200", 3000, "Active", None),
        ("EMP006", "Magdalena Grabowska", "Finance & Accounting", "CC-200", 2500, "Active", None),
        ("EMP007", "Tomasz Zajac", "Finance & Accounting", "CC-200", 4000, "Active", None),
        ("EMP008", "Agnieszka Krol", "Sales & Commercial", "CC-300", 6000, "Active", None),
        ("EMP009", "Pawel Wieczorek", "Sales & Commercial", "CC-300", 5500, "Active", None),
        ("EMP010", "Monika Jablonska", "Sales & Commercial", "CC-300", 5000, "Active", None),
        ("EMP011", "Krzysztof Wrobel", "Sales & Commercial", "CC-300", 4500, "Active", None),
        ("EMP012", "Karolina Nowakowska", "Sales & Commercial", "CC-300", 6000, "Active", None),
        ("EMP013", "Marcin Majewski", "HR & Administration", "CC-400", 2500, "Active", None),
        ("EMP014", "Ewa Olszewska", "HR & Administration", "CC-400", 3000, "Active", None),
        ("EMP015", "Jakub Stepien", "HR & Administration", "CC-400", 2000, "Active", None),
        ("EMP016", "Natalia Jaworska", "Medical Equipment R&D", "CC-500", 5000, "Active", None),
        ("EMP017", "Lukasz Malinowski", "Medical Equipment R&D", "CC-500", 4500, "Active", None),
        ("EMP018", "Aleksandra Pawlak", "Medical Equipment R&D", "CC-500", 4000, "Active", None),
        ("EMP019", "Grzegorz Gorski", "Medical Equipment R&D", "CC-500", 3500, "Active", None),
        ("EMP020", "Dorota Witkowska", "IT & Cloud Infrastructure", "CC-100", 3000, "Active", None),
        ("EMP021", "Wojciech Walczak", "Sales & Commercial", "CC-300", 5000, "Active", None),
        ("EMP022", "Barbara Sikora", "Finance & Accounting", "CC-200", 3000, "Active", None),
        ("EMP023", "Robert Baran", "Sales & Commercial", "CC-300", 4000, "Terminated", "2026-09-15"),
        ("EMP024", "Zofia Rutkowska", "IT & Cloud Infrastructure", "CC-100", 3500, "Terminated", "2026-09-30"),
        ("EMP025", "Damian Michalak", "Medical Equipment R&D", "CC-500", 4500, "Terminated", "2026-10-05"),
    ]

    df_employees = pd.DataFrame(
        employees,
        columns=[
            "emp_id",
            "full_name",
            "department",
            "cost_center_id",
            "monthly_limit_pln",
            "status",
            "termination_date",
        ],
    )
    df_cost_centers = pd.DataFrame(cost_centers)

    excel_path = RAW_DATA_DIR / "hr_employee_directory.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_employees.to_excel(writer, sheet_name="Employees", index=False)
        df_cost_centers.to_excel(writer, sheet_name="Cost_Centers", index=False)

    print(f"[OK] Generated HR directory file: {excel_path}")
    return df_employees


def dirty_date(date_obj: datetime) -> str:
    """Convert a datetime object into a randomly chosen inconsistent date string format."""
    fmt = random.choice(["%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"])
    return date_obj.strftime(fmt)


def dirty_amount(amount: float) -> str:
    """Format a float amount with inconsistent separators (dots, commas, thousand spaces)."""
    style = random.choice(["standard", "comma", "space_comma"])
    if style == "standard":
        return f"{amount:.2f}"
    elif style == "comma":
        return f"{amount:.2f}".replace(".", ",")
    else:
        return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


def dirty_id(identifier: str) -> str:
    """Add random leading/trailing whitespace or lowercase characters to an ID."""
    variation = random.choice(["clean", "spaces", "lower_spaces"])
    if variation == "clean":
        return identifier
    elif variation == "spaces":
        return f"  {identifier} "
    else:
        return f" {identifier.lower()}  "


def generate_sap_expenses(df_employees: pd.DataFrame) -> None:
    """Generate a raw SAP expenses CSV extract containing technical and business anomalies."""
    vendors_and_descriptions = [
        ("Lufthansa", "Business flight to Frankfurt"),
        ("Hotel Marriott", "Conference hotel accommodation"),
        ("Uber", "Airport transfer"),
        ("PKP Intercity", "Train ticket Warsaw-Wroclaw"),
        ("Orlen", "Company car fuel"),
        ("Amazon Web Services", "Cloud hosting subscription"),
        ("Moonsfera Restaurant", "Client business dinner"),
        ("Dell Poland", "IT hardware accessories"),
        ("Allegro Corporate", "Office supplies"),
        ("Hilton Hotels", "Business trip lodging"),
    ]

    currencies = ["PLN", "PLN", "PLN", "EUR", "USD"]
    rows = []
    tx_counter = 1001

    active_employees = df_employees[df_employees["status"] == "Active"].to_dict("records")

    start_date = datetime(2026, 10, 1)
    for _ in range(230):
        emp = random.choice(active_employees)
        vendor, description = random.choice(vendors_and_descriptions)
        currency = random.choice(currencies)

        if currency == "PLN":
            amount = round(random.uniform(40.0, 450.0), 2)
        elif currency == "EUR":
            amount = round(random.uniform(15.0, 120.0), 2)
        else:
            amount = round(random.uniform(20.0, 130.0), 2)

        tx_date = start_date + timedelta(days=random.randint(0, 24))

        rows.append([
            dirty_id(f"TX{tx_counter}"),
            dirty_id(emp["emp_id"]),
            dirty_id(emp["cost_center_id"]),
            dirty_date(tx_date),
            dirty_amount(amount),
            dirty_id(currency),
            f" {vendor} " if random.random() < 0.3 else vendor,
            description,
        ])
        tx_counter += 1


    terminated_anomalies = [
        ("EMP023", "CC-300", datetime(2026, 10, 2), 1250.50, "PLN", "Hotel Marriott", "Conference hotel accommodation"),
        ("EMP023", "CC-300", datetime(2026, 10, 12), 450.00, "EUR", "Lufthansa", "Business flight to Frankfurt"),
        ("EMP024", "CC-100", datetime(2026, 10, 10), 890.00, "PLN", "Dell Poland", "IT hardware accessories"),
        ("EMP025", "CC-500", datetime(2026, 10, 18), 320.00, "USD", "Amazon Web Services", "Cloud hosting subscription"),
    ]
    for emp_id, cc_id, dt, amt, curr, vend, desc in terminated_anomalies:
        rows.append([
            f"TX{tx_counter}",
            dirty_id(emp_id),
            dirty_id(cc_id),
            dirty_date(dt),
            dirty_amount(amt),
            curr,
            vend,
            desc,
        ])
        tx_counter += 1

    overrun_anomalies = [
        ("EMP005", "CC-200", datetime(2026, 10, 14), 1200.00, "EUR", "Lufthansa", "Business class flight upgrade"),
        ("EMP015", "CC-400", datetime(2026, 10, 16), 2850.00, "PLN", "Hilton Hotels", "Executive HR summit lodging"),
        ("EMP002", "CC-100", datetime(2026, 10, 19), 1100.00, "USD", "Dell Poland", "Mobile workstation purchase"),
    ]
    for emp_id, cc_id, dt, amt, curr, vend, desc in overrun_anomalies:
        rows.append([
            f"TX{tx_counter}",
            dirty_id(emp_id),
            dirty_id(cc_id),
            dirty_date(dt),
            dirty_amount(amt),
            curr,
            vend,
            desc,
        ])
        tx_counter += 1

    duplicate_pairs = [
        ("EMP008", "CC-300", datetime(2026, 10, 11), 1450.00, "PLN", "Moonsfera Restaurant", "Client dinner - duplicate billing"),
        ("EMP016", "CC-500", datetime(2026, 10, 20), 620.50, "EUR", "Lufthansa", "Flight ticket - double charge"),
    ]
    for emp_id, cc_id, dt, amt, curr, vend, desc in duplicate_pairs:
        rows.append([
            f"TX{tx_counter}",
            emp_id,
            cc_id,
            dt.strftime("%Y-%m-%d"),
            dirty_amount(amt),
            curr,
            vend,
            desc,
        ])
        tx_counter += 1
        rows.append([
            f"TX{tx_counter}",
            f" {emp_id} ",
            cc_id,
            dt.strftime("%d.%m.%Y"),
            f"{amt:.2f}",
            curr,
            f" {vend}",
            desc,
        ])
        tx_counter += 1

    cc_mismatch_anomalies = [
        ("EMP001", "CC-300", datetime(2026, 10, 7), 540.00, "PLN", "Uber", "Charged to Sales instead of IT"),
        ("EMP009", "CC-100", datetime(2026, 10, 9), 780.00, "PLN", "Orlen", "Charged to IT instead of Sales"),
        ("EMP013", "CC-999", datetime(2026, 10, 21), 1120.00, "PLN", "Allegro Corporate", "Invalid cost center CC-999"),
        ("EMP017", "CC-888", datetime(2026, 10, 22), 310.00, "EUR", "Hotel Marriott", "Unrecognized SAP cost center"),
    ]
    for emp_id, wrong_cc, dt, amt, curr, vend, desc in cc_mismatch_anomalies:
        rows.append([
            f"TX{tx_counter}",
            dirty_id(emp_id),
            dirty_id(wrong_cc),
            dirty_date(dt),
            dirty_amount(amt),
            curr,
            vend,
            desc,
        ])
        tx_counter += 1

    corrupted_rows = [
        ["", "EMP003", "CC-100", "2026-10-12", "250,00", "PLN", "Uber", "Missing transaction ID"],
        ["   ", "EMP010", "CC-300", "15.10.2026", "120.00", "EUR", "Lufthansa", "Whitespace transaction ID"],
        [f"TX{tx_counter}", "EMP004", "CC-100", "2026-10-18", "-450,00", "PLN", "Orlen", "Invalid negative expense"],
        [f"TX{tx_counter + 1}", "EMP012", "CC-300", "2026/10/19", "-85.50", "USD", "Hilton Hotels", "Negative charge error"],
        [f"TX{tx_counter + 2}", "", "CC-200", "2026-10-20", "300,00", "PLN", "PKP Intercity", "Missing employee ID"],
    ]
    rows.extend(corrupted_rows)

    rows.append(rows[0])
    rows.append(rows[15])

    random.shuffle(rows)

    csv_path = RAW_DATA_DIR / "sap_expenses_extract.csv"
    headers = ["tx_id", "emp_id", "cost_center_id", "tx_date", "amount", "currency", "vendor", "description"]

    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        for idx, row in enumerate(rows):
            writer.writerow(row)
            if idx in (50, 120, 190):
                writer.writerow([])

    print(f"[OK] Generated SAP CSV extract: {csv_path} (total lines: {len(rows) + 4})")


def main() -> None:
    print("--- Starting Mock Data Generation (Module 1) ---")
    create_directories()
    df_employees = generate_hr_data()
    generate_sap_expenses(df_employees)
    print("--- Mock Data Generation Completed Successfully ---")


if __name__ == "__main__":
    main()