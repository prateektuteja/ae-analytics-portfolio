#!/usr/bin/env python3
"""
Day 8 — migrate generic test args to the `arguments:` nested syntax, silencing
MissingArgumentsPropertyInGenericTestDeprecation.

Old style:
    - relationships:
        to: ref('dim_customers')
        field: customer_id

New style:
    - relationships:
        arguments:
          to: ref('dim_customers')
          field: customer_id

Scans every models/**/*.yml file (staging/intermediate/marts), finds any test
entry whose config dict has un-nested argument keys, and nests them under
`arguments:`. Reserved keys (config, description, name, arguments) are left
at the top level — only nests genuine argument keys (to, field, values,
combination_of_columns, column_name, etc.).

Idempotent: a test already using `arguments:` is left untouched.

Run from the dbt project root:
    cd ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/
    python migrate_test_arguments_syntax.py
"""

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_GLOB = "models/**/*.yml"

# Keys that are NOT test arguments and must stay at the top level of a test's config.
RESERVED_KEYS = {"arguments", "config", "description", "name"}


def migrate_test_entry(test_entry):
    """
    test_entry is one item from a `tests:` list, e.g.:
        {"relationships": {"to": "ref('dim_customers')", "field": "customer_id"}}
    or the bare string "not_null" / "unique" (no args, nothing to do).
    Returns (new_entry, changed: bool).
    """
    if isinstance(test_entry, str):
        return test_entry, False

    if not isinstance(test_entry, dict) or len(test_entry) != 1:
        return test_entry, False

    (test_name, config), = test_entry.items()

    if config is None:
        return test_entry, False

    if not isinstance(config, dict):
        # e.g. some tests take a bare value; nothing to nest
        return test_entry, False

    if "arguments" in config:
        return test_entry, False  # already migrated

    arg_keys = [k for k in config if k not in RESERVED_KEYS]
    if not arg_keys:
        return test_entry, False  # nothing to migrate (only reserved keys present)

    new_config = {k: v for k, v in config.items() if k in RESERVED_KEYS}
    new_config["arguments"] = {k: config[k] for k in arg_keys}

    # keep reserved keys before arguments for readability where present
    ordered = {}
    for k in ("description", "config", "arguments", "name"):
        if k in new_config:
            ordered[k] = new_config[k]

    return {test_name: ordered}, True


def migrate_tests_list(tests_list):
    changed_any = False
    new_list = []
    for entry in tests_list:
        new_entry, changed = migrate_test_entry(entry)
        new_list.append(new_entry)
        changed_any = changed_any or changed
    return new_list, changed_any


def migrate_model_entry(model_entry, file_label):
    changed = False

    if "tests" in model_entry:
        new_tests, c = migrate_tests_list(model_entry["tests"])
        if c:
            model_entry["tests"] = new_tests
            changed = True

    for col in model_entry.get("columns", []) or []:
        if "tests" in col:
            new_tests, c = migrate_tests_list(col["tests"])
            if c:
                col["tests"] = new_tests
                changed = True
                print(f"  migrated: {model_entry.get('name')}.{col.get('name')} in {file_label}")

    return changed


def patch_file(path):
    rel = path.relative_to(PROJECT_ROOT)
    with open(path) as f:
        doc = yaml.safe_load(f)

    if not doc or "models" not in doc:
        return

    file_changed = False
    for model_entry in doc["models"]:
        if migrate_model_entry(model_entry, str(rel)):
            file_changed = True

    if not file_changed:
        print(f"No changes needed: {rel}")
        return

    backup = path.with_suffix(path.suffix + ".bak2")
    backup.write_text(path.read_text())
    print(f"Backup written: {backup}")

    with open(path, "w") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False, width=100)
    print(f"Wrote: {rel}")


def main():
    yml_files = sorted(PROJECT_ROOT.glob(MODELS_GLOB))
    if not yml_files:
        print(f"No yml files found under {PROJECT_ROOT / 'models'}")
        return 1

    for path in yml_files:
        patch_file(path)

    print("\nDone. Now run:")
    print("  dbt parse   # confirm MissingArgumentsPropertyInGenericTestDeprecation is gone")
    print("  dbt test    # confirm everything still passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
