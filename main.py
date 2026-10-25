import importlib
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

# Add src/ directory to sys.path for dynamic module loading
sys.path.insert(0, str(SRC_DIR))


def run_pipeline() -> None:
    """Execute the complete Finance & HR Data Reconciliation Pipeline."""
    start_time = time.perf_counter()

    print("=================================================================")
    print("   FINANCE & HR DATA RECONCILIATION PIPELINE - EXECUTION START   ")
    print("=================================================================\n")

    pipeline_steps = [
        ("Step 1/3: Mock Data Generation", "01_generate_mock_data"),
        ("Step 2/3: ETL & Data Cleaning", "02_etl_and_clean"),
        ("Step 3/3: SQL Reconciliation & Excel Reporting", "03_run_checks_and_report"),
    ]

    for step_label, module_name in pipeline_steps:
        print(f">>> {step_label} ({module_name}.py)")
        module = importlib.import_module(module_name)
        module.main()
        print()

    elapsed = time.perf_counter() - start_time
    print("=================================================================")
    print(f"   PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print("=================================================================")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as exc:
        print(f"\n[ERROR] Pipeline execution failed: {exc}", file=sys.stderr)
        sys.exit(1)