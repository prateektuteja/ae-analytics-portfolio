#!/usr/bin/env python3
"""
Day 8 — add dbt_utils.unique_combination_of_columns composite-key tests to:
  - models/staging/stg_models.yml       -> stg_payments, stg_order_items
  - models/intermediate/int_models.yml  -> int_order_items
  - models/marts/marts_model.yml        -> fct_order_items

Same MODELS-dict / write_model() pattern as write_dim_tests.py / write_int_tests.py.
Idempotent: skips a model if it already has a dbt_utils.unique_combination_of_columns test.

Run from the dbt project root:
    cd ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/
    python write_day8_composite_tests.py
"""

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent

TARGETS = {
    "models/staging/stg_models.yml": [
        {
            "model": "stg_payments",
            "combination_of_columns": ["order_id", "payment_sequential"],
            "new_description": (
                "Composite key (order_id, payment_sequential). Composite uniqueness "
                "enforced via dbt_utils.unique_combination_of_columns. Profiling "
                "confirmed no nulls in any column."
            ),
        },
        {
            "model": "stg_order_items",
            "combination_of_columns": ["order_id", "order_item_id"],
            "new_description": (
                "Composite key (order_id, order_item_id). Composite uniqueness "
                "enforced via dbt_utils.unique_combination_of_columns. Profiling "
                "confirmed no nulls in any column."
            ),
        },
    ],
    "models/intermediate/int_models.yml": [
        {
            "model": "int_order_items",
            "combination_of_columns": ["order_id", "order_item_id"],
        },
    ],
    "models/marts/marts_model.yml": [
        {
            "model": "fct_order_items",
            "combination_of_columns": ["order_id", "order_item_id"],
        },
    ],
}


def build_test_block(combination_of_columns):
    return {
        "dbt_utils.unique_combination_of_columns": {
            "arguments": {"combination_of_columns": list(combination_of_columns)}
        }
    }


def has_composite_test(model_entry):
    for t in model_entry.get("tests", []):
        if isinstance(t, dict) and "dbt_utils.unique_combination_of_columns" in t:
            return True
    return False


def patch_file(rel_path, edits):
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        print(f"SKIP (not found): {rel_path}")
        return

    with open(path) as f:
        doc = yaml.safe_load(f) or {}

    models = doc.get("models", [])
    edits_by_name = {e["model"]: e for e in edits}
    touched = False

    for model_entry in models:
        name = model_entry.get("name")
        if name not in edits_by_name:
            continue
        edit = edits_by_name[name]

        if has_composite_test(model_entry):
            print(f"SKIP (already has composite test): {name} in {rel_path}")
            continue

        test_block = build_test_block(edit["combination_of_columns"])
        model_entry.setdefault("tests", [])
        model_entry["tests"].append(test_block)

        if "new_description" in edit:
            model_entry["description"] = edit["new_description"]

        # move 'tests' key to sit right after 'description'/'name' for readability
        ordered = {}
        for key in ("name", "description", "tests", "columns"):
            if key in model_entry:
                ordered[key] = model_entry[key]
        for key in model_entry:
            if key not in ordered:
                ordered[key] = model_entry[key]
        model_entry.clear()
        model_entry.update(ordered)

        touched = True
        print(f"PATCHED: {name} in {rel_path}")

    if not touched:
        print(f"No changes made to {rel_path}")
        return

    backup = path.with_suffix(path.suffix + ".bak")
    backup.write_text(path.read_text())
    print(f"Backup written: {backup}")

    with open(path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False, width=100)
    print(f"Wrote: {path}")


def main():
    for rel_path, edits in TARGETS.items():
        patch_file(rel_path, edits)
    print("\nDone. Now run:")
    print(
        "  dbt test --select stg_payments stg_order_items int_order_items fct_order_items"
    )


if __name__ == "__main__":
    sys.exit(main())
