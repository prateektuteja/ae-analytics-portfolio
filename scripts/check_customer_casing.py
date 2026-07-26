import duckdb, os

con = duckdb.connect(os.path.expanduser("~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/dev.duckdb"))

print("=== customer_city casing variants ===")
print(con.execute("""
    select lower(trim(customer_city)) as norm, count(distinct customer_city) as variants
    from raw_customers group by 1 having count(distinct customer_city) > 1 limit 10
""").df())

print("\n=== customer_state distinct values ===")
print(con.execute("select distinct customer_state from raw_customers order by 1").df())

print("\n=== customer_id null/duplicate check ===")
print(con.execute("select count(*) - count(customer_id) as nulls from raw_customers").fetchone())
print(con.execute("""
    select customer_id, count(*) as cnt from raw_customers
    group by customer_id having count(*) > 1 limit 5
""").df())
