"""
Writes models/intermediate/int_order_items_summary.sql for the
ae_analytics_portfolio dbt project.

Run this from anywhere on your machine (it uses a relative path assuming
you run it from the dbt project root: ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/).
Adjust PROJECT_ROOT below if you'd rather run it from elsewhere.
"""

from pathlib import Path

# Adjust if not running from inside the dbt project root
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "intermediate" / "int_order_items_summary.sql"

SQL = """select
    order_id,
    count(*) as item_count,
    sum(price) as total_item_value,
    sum(freight_value) as total_freight_value
from {{ ref('stg_order_items') }}
group by order_id
"""

def main():
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if MODEL_PATH.exists():
        overwrite = input(f"{MODEL_PATH} already exists. Overwrite? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Skipped — no changes made.")
            return

    MODEL_PATH.write_text(SQL)
    print(f"Wrote {MODEL_PATH}")


if __name__ == "__main__":
    main()
