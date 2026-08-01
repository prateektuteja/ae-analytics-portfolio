"""
Day 6 mart validation — dim_customers, dim_sellers, dim_products, fct_orders.

Connects directly to the project's DuckDB file (same pattern as
validate_int_order_payments.py from Day 5) and runs:
  1. Row-count parity: each mart vs. distinct-key count on its staging source
  2. dim_products join fan-out check (duplicate category names on the
     translation table would inflate the join)
  3. Spot-check fct_orders measures against known-good orders already
     validated in Day 5 (int_order_payments / int_order_items_summary)
  4. Null check on fct_orders.total_paid_amount (expected only for orders
     with zero payment rows, e.g. cancelled-before-payment)

Run this from the same directory as validate_int_order_payments.py.
"""

from pathlib import Path
from typing import Optional

import duckdb

DB_PATH = Path(__file__).resolve().parent / "dev.duckdb"

# Known-good orders already validated in Day 5 (truncated prefixes from
# int_order_payments spot checks)
KNOWN_ORDERS = [
    "465c2e1bee4561cb3",  # single credit card, 12 payment rows
    "3a096d99346df2d6c",  # two credit cards
]


def resolve_full_order_id(con, prefix: str) -> Optional[str]:
    """Resolve a truncated order_id prefix to its full value, safely.

    Mirrors the ilike-safety gotcha from Day 5: always confirm the prefix
    matches exactly one order before trusting it.
    """
    rows = con.execute(
        "select distinct order_id from stg_orders where order_id ilike ?",
        [f"{prefix}%"],
    ).fetchall()
    if len(rows) == 0:
        print(f"  ⚠ no order found matching prefix {prefix}")
        return None
    if len(rows) > 1:
        print(f"  ⚠ prefix {prefix} matches {len(rows)} orders — ambiguous, skipping")
        return None
    return rows[0][0]


def check_row_count_parity(con):
    print("\n=== 1. Row-count parity ===")
    checks = [
        ("dim_customers", "select count(*) from dim_customers",
         "stg_customers distinct customer_id", "select count(distinct customer_id) from stg_customers"),
        ("dim_sellers", "select count(*) from dim_sellers",
         "stg_sellers distinct seller_id", "select count(distinct seller_id) from stg_sellers"),
        ("dim_products", "select count(*) from dim_products",
         "stg_products distinct product_id", "select count(distinct product_id) from stg_products"),
        ("fct_orders", "select count(*) from fct_orders",
         "stg_orders distinct order_id", "select count(distinct order_id) from stg_orders"),
    ]
    all_ok = True
    for mart_name, mart_sql, source_label, source_sql in checks:
        mart_count = con.execute(mart_sql).fetchone()[0]
        source_count = con.execute(source_sql).fetchone()[0]
        status = "OK" if mart_count == source_count else "MISMATCH"
        if status == "MISMATCH":
            all_ok = False
        print(f"  {mart_name}: {mart_count}  vs.  {source_label}: {source_count}  [{status}]")
    return all_ok


def check_dim_products_fanout(con):
    print("\n=== 2. dim_products join fan-out check ===")
    dupes = con.execute(
        """
        select product_category_name, count(*) as n
        from stg_product_category_translation
        group by 1
        having count(*) > 1
        """
    ).fetchall()
    if dupes:
        print(f"  ⚠ {len(dupes)} duplicate category name(s) in translation table — likely fan-out cause:")
        for row in dupes:
            print(f"    {row}")
        return False
    print("  OK — no duplicate category names in stg_product_category_translation")
    return True


def check_known_orders(con):
    print("\n=== 3. Spot-check known orders in fct_orders ===")
    all_ok = True
    for prefix in KNOWN_ORDERS:
        order_id = resolve_full_order_id(con, prefix)
        if order_id is None:
            all_ok = False
            continue
        fct_row = con.execute(
            """
            select total_paid_amount, payment_installments_count, credit_card_count,
                   item_count, total_item_value, total_freight_value
            from fct_orders where order_id = ?
            """,
            [order_id],
        ).fetchone()
        payments_row = con.execute(
            "select total_paid_amount, payment_installments_count, credit_card_count from int_order_payments where order_id = ?",
            [order_id],
        ).fetchone()
        items_row = con.execute(
            "select item_count, total_item_value, total_freight_value from int_order_items_summary where order_id = ?",
            [order_id],
        ).fetchone()

        payments_match = fct_row[:3] == payments_row
        items_match = fct_row[3:] == items_row
        status = "OK" if (payments_match and items_match) else "MISMATCH"
        if status == "MISMATCH":
            all_ok = False
        print(f"  order {order_id[:17]}...: fct_orders={fct_row}")
        print(f"    vs int_order_payments={payments_row}, int_order_items_summary={items_row}  [{status}]")
    return all_ok


def check_null_payment_totals(con):
    print("\n=== 4. Null total_paid_amount check ===")
    null_count = con.execute(
        "select count(*) from fct_orders where total_paid_amount is null"
    ).fetchone()[0]
    print(f"  {null_count} order(s) with null total_paid_amount")
    if null_count > 0:
        sample = con.execute(
            "select order_id, order_status from fct_orders where total_paid_amount is null limit 5"
        ).fetchall()
        print("  Sample (expect cancelled/unpaid statuses):")
        for row in sample:
            print(f"    {row}")
    return True  # informational, not pass/fail


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    results = [
        check_row_count_parity(con),
        check_dim_products_fanout(con),
        check_known_orders(con),
        check_null_payment_totals(con),
    ]
    con.close()
    print("\n=== Summary ===")
    print("ALL CHECKS PASSED" if all(results) else "SOME CHECKS FAILED — see above")


if __name__ == "__main__":
    main()
