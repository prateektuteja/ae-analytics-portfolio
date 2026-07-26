import duckdb, os

con = duckdb.connect(os.path.expanduser("~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/dev.duckdb"))

print("=== raw_orders: null counts ===")
cols = con.execute("select column_name from information_schema.columns where table_name = 'raw_orders'").df()["column_name"].tolist()
null_exprs = ", ".join([f"count(*) - count({c}) as {c}" for c in cols])
nulls = con.execute(f"select {null_exprs} from raw_orders").df().T
nulls.columns = ["null_count"]
print(nulls[nulls["null_count"] > 0] if (nulls["null_count"] > 0).any() else "none")

print("\n=== raw_orders: order_id duplicate check ===")
print(con.execute("select order_id, count(*) as cnt from raw_orders group by order_id having count(*) > 1 limit 5").df())

print("\n=== raw_products: null counts ===")
cols = con.execute("select column_name from information_schema.columns where table_name = 'raw_products'").df()["column_name"].tolist()
null_exprs = ", ".join([f"count(*) - count({c}) as {c}" for c in cols])
nulls = con.execute(f"select {null_exprs} from raw_products").df().T
nulls.columns = ["null_count"]
print(nulls[nulls["null_count"] > 0] if (nulls["null_count"] > 0).any() else "none")

print("\n=== raw_products: product_id duplicate check ===")
print(con.execute("select product_id, count(*) as cnt from raw_products group by product_id having count(*) > 1 limit 5").df())
