#!/usr/bin/env python3
"""
Day 8 — Python edge-case validation.

Complements today's dbt tests (composite-key uniqueness + 2 singular tests)
with checks that are deliberately done a *different* way than the SQL tests,
not just re-running the same query in Python:

  1. Full-population payment reconciliation: for EVERY order (not just the
     2 known orders spot-checked on Day 5), recompute total_paid_amount by
     summing raw_payments.payment_value in pandas and compare against
     fct_orders.total_paid_amount with a float tolerance. Catches a bug that
     would slip through if the same rounding/scoping mistake existed in both
     the dbt model and a SQL-based test (independent implementation, same
     defensive logic as validate_int_order_payments.py's math.isclose usage,
     just scaled to the whole table instead of 2 rows).

  2. Composite-grain row-count parity across the whole order_items pipeline:
     raw_order_items -> stg_order_items -> int_order_items -> fct_order_items.
     Confirms the new dbt_utils.unique_combination_of_columns tests (Day 8)
     aren't just "no duplicates" but also "no silent row loss/fan-out" at
     each layer for the (order_id, order_item_id) grain.

  3. Orphan re-check (fct_order_items vs fct_orders) done via a pandas
     anti-join, independently of the assert_no_orphaned_order_items.sql
     singular test added today.

Run from the dbt project root (same DB_PATH convention as
validate_int_order_payments.py / validate_marts_day6.py):
    cd ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/
    python validate_day8_edge_cases.py
"""

import math
import sys
from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "dev.duckdb"
TOLERANCE = 0.01  # currency comparisons, same tolerance as validate_int_order_payments.py


def get_conn() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        print(f"ERROR: duckdb file not found at {DB_PATH}")
        print("Adjust DB_PATH if dev.duckdb lives elsewhere in this project.")
        sys.exit(1)
    return duckdb.connect(str(DB_PATH), read_only=True)


def check_payment_reconciliation(con: duckdb.DuckDBPyConnection) -> bool:
    print("\n[1] Full-population payment reconciliation (raw_payments vs fct_orders)")

    raw_payments = con.execute("select order_id, payment_value from raw_payments").df()
    fct_orders = con.execute(
        "select order_id, total_paid_amount from fct_orders"
    ).df()

    recomputed = (
        raw_payments.groupby("order_id", as_index=False)["payment_value"]
        .sum()
        .rename(columns={"payment_value": "recomputed_total"})
    )

    merged = fct_orders.merge(recomputed, on="order_id", how="left")
    # orders with zero payment rows: recomputed_total will be NaN -> treat as 0
    merged["recomputed_total"] = merged["recomputed_total"].fillna(0.0)
    merged["total_paid_amount"] = merged["total_paid_amount"].fillna(0.0)

    def mismatched(row) -> bool:
        return not math.isclose(
            row["total_paid_amount"], row["recomputed_total"], abs_tol=TOLERANCE
        )

    merged["mismatch"] = merged.apply(mismatched, axis=1)
    bad = merged[merged["mismatch"]]

    if bad.empty:
        print(f"  PASS — all {len(merged)} orders reconcile within ${TOLERANCE}")
        return True

    print(f"  FAIL — {len(bad)} / {len(merged)} orders do not reconcile:")
    print(bad.head(10).to_string(index=False))
    return False


def check_row_count_parity(con: duckdb.DuckDBPyConnection) -> bool:
    print("\n[2] Composite-grain row-count parity: raw -> stg -> int -> fct (order_items)")

    counts = {
        "raw_order_items": con.execute(
            "select count(distinct (order_id, order_item_id)) from raw_order_items"
        ).fetchone()[0],
        "stg_order_items": con.execute(
            "select count(distinct (order_id, order_item_id)) from stg_order_items"
        ).fetchone()[0],
        "int_order_items": con.execute(
            "select count(distinct (order_id, order_item_id)) from int_order_items"
        ).fetchone()[0],
        "fct_order_items": con.execute(
            "select count(distinct (order_id, order_item_id)) from fct_order_items"
        ).fetchone()[0],
    }

    for layer, n in counts.items():
        print(f"  {layer:<20} {n}")

    baseline = counts["raw_order_items"]
    all_match = all(n == baseline for n in counts.values())

    if all_match:
        print("  PASS — row count identical across every layer")
    else:
        print("  FAIL — row count drifted somewhere in the pipeline")

    return all_match


def check_orphans_pandas(con: duckdb.DuckDBPyConnection) -> bool:
    print("\n[3] Orphan re-check via pandas anti-join (fct_order_items vs fct_orders)")

    items = con.execute("select order_id, order_item_id from fct_order_items").df()
    orders = con.execute("select order_id from fct_orders").df()
    orders["_in_fct_orders"] = True

    merged = items.merge(orders, on="order_id", how="left")
    orphans = merged[merged["_in_fct_orders"].isna()]

    if orphans.empty:
        print(f"  PASS — 0 orphaned rows across {len(items)} fct_order_items rows")
        return True

    print(f"  FAIL — {len(orphans)} orphaned rows found:")
    print(orphans.head(10).to_string(index=False))
    return False


def main() -> int:
    con = get_conn()
    results = [
        check_payment_reconciliation(con),
        check_row_count_parity(con),
        check_orphans_pandas(con),
    ]
    con.close()

    print("\n" + "=" * 60)
    if all(results):
        print("ALL DAY 8 EDGE-CASE CHECKS PASSED")
        return 0
    else:
        print("ONE OR MORE CHECKS FAILED — see details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
