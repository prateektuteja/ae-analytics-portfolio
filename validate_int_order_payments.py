"""
Validates int_order_payments against the two known-good orders manually
profiled during Day 5 design (see Mart_Spec_Draft.md):

  - 465c2e1bee4561cb3... : single credit_card row (11 voucher rows + 1
    credit_card row, installments=5) -> total_paid_amount reconciles to
    879.44 exactly; payment_installments_count should be 5, not the naive
    16 you'd get summing installments across all rows.
  - 3a096d99346df2d6c... : two credit_card rows (10 + 1 installments)
    -> payment_installments_count should be 11 (sum scoped to credit_card
    rows only), credit_card_count should be 2.

Run from the dbt project root:
    python validate_int_order_payments.py

Requires: pip install duckdb --break-system-packages (if not already installed)
"""

import math
from pathlib import Path

import duckdb

# Fields compared with tolerance (float/currency) vs. exact equality (ints, bools)
FLOAT_FIELDS = {"total_paid_amount"}

# --- Adjust this if your DuckDB file lives somewhere else ---
# Check ~/.dbt/profiles.yml under this project's profile for the exact
# `path:` value if this default doesn't match.
DB_PATH = Path(__file__).resolve().parent / "dev.duckdb"

TEST_CASES = [
    {
        "label": "single credit_card order (11 voucher + 1 credit_card)",
        "order_id_prefix": "465c2e1bee4561cb3",
        "expect": {
            "total_paid_amount": 879.44,
            "payment_installments_count": 5,
            "credit_card_count": 1,
            "payment_installment_opted": True,
            "distinct_payment_types_count": 2,
        },
    },
    {
        "label": "two-credit_card order (10 + 1 installments)",
        "order_id_prefix": "3a096d99346df2d6c",
        "expect": {
            "payment_installments_count": 11,
            "credit_card_count": 2,
            "payment_installment_opted": True,
        },
    },
]


def resolve_order_id(con, prefix: str) -> str:
    """Resolve a truncated order_id prefix to its full id, refusing to
    proceed if the prefix isn't unique (same gotcha logged in
    PROJECT_FACTS.md re: ilike partial-match risk)."""
    matches = con.execute(
        "select distinct order_id from int_order_payments where order_id like ?",
        [f"{prefix}%"],
    ).fetchall()

    if len(matches) == 0:
        raise ValueError(f"No order_id found matching prefix '{prefix}'")
    if len(matches) > 1:
        raise ValueError(
            f"Prefix '{prefix}' matches {len(matches)} distinct order_ids "
            f"— not safe to assume which one. Use a longer/exact prefix."
        )
    return matches[0][0]


def run_test_case(con, case: dict) -> bool:
    order_id = resolve_order_id(con, case["order_id_prefix"])

    row = con.execute(
        """
        select
            total_paid_amount,
            payment_installments_count,
            credit_card_count,
            payment_installment_opted,
            distinct_payment_types_count
        from int_order_payments
        where order_id = ?
        """,
        [order_id],
    ).fetchone()

    if row is None:
        print(f"FAIL — {case['label']}: order_id {order_id} not found in int_order_payments")
        return False

    columns = [
        "total_paid_amount",
        "payment_installments_count",
        "credit_card_count",
        "payment_installment_opted",
        "distinct_payment_types_count",
    ]
    actual = dict(zip(columns, row))

    all_passed = True
    print(f"\n{case['label']}  (order_id: {order_id})")
    for field, expected_value in case["expect"].items():
        actual_value = actual[field]
        if field in FLOAT_FIELDS:
            ok = math.isclose(actual_value, expected_value, abs_tol=0.01)
        else:
            ok = actual_value == expected_value
        all_passed &= ok
        status = "OK" if ok else "MISMATCH"
        print(f"  [{status}] {field}: expected={expected_value} actual={actual_value}")

    return all_passed


def main():
    if not DB_PATH.exists():
        print(f"DuckDB file not found at {DB_PATH} — update DB_PATH at the top of this script.")
        return

    con = duckdb.connect(str(DB_PATH), read_only=True)

    results = [run_test_case(con, case) for case in TEST_CASES]

    print("\n" + "=" * 50)
    if all(results):
        print(f"All {len(results)} test cases passed.")
    else:
        failed = results.count(False)
        print(f"{failed} of {len(results)} test case(s) failed — see MISMATCH lines above.")


if __name__ == "__main__":
    main()
