import duckdb, os

con = duckdb.connect(os.path.expanduser("~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/dev.duckdb"))

tables = {
    "raw_payments": ["order_id", "payment_sequential"],
    "raw_reviews": ["review_id"],
    "raw_sellers": ["seller_id"],
    "raw_order_items": ["order_id", "order_item_id"],
    "raw_product_category_translation": ["product_category_name"],
}

for tbl, pk in tables.items():
    print(f"\n=== {tbl} ===")
    cols = con.execute(
        f"select column_name from information_schema.columns where table_name = '{tbl}'"
    ).df()["column_name"].tolist()

    total = con.execute(f"select count(*) from {tbl}").fetchone()[0]
    print(f"total rows: {total}")

    null_exprs = ", ".join([f"count(*) - count({c}) as {c}" for c in cols])
    nulls = con.execute(f"select {null_exprs} from {tbl}").df().T
    nulls.columns = ["null_count"]
    print("null counts per column:")
    print(nulls[nulls["null_count"] > 0] if (nulls["null_count"] > 0).any() else "none")

    pk_cols = ", ".join(pk)
    dupes = con.execute(f"""
        select {pk_cols}, count(*) as cnt
        from {tbl}
        group by {pk_cols}
        having count(*) > 1
        limit 5
    """).df()
    print(f"duplicate {pk} check:")
    print(dupes if not dupes.empty else "none found — candidate key looks unique")

print("\n=== seller_city / seller_state casing variants ===")
print(con.execute("""
    select lower(trim(seller_city)) as norm, count(distinct seller_city) as variants
    from raw_sellers group by 1 having count(distinct seller_city) > 1 limit 10
""").df())

print("\n=== payment_type distinct values ===")
print(con.execute("select distinct payment_type from raw_payments").df())

print("\n=== review_score distinct values (expect 1-5) ===")
print(con.execute("select distinct review_score from raw_reviews order by 1").df())
