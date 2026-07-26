import duckdb, os

con = duckdb.connect(os.path.expanduser("~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/dev.duckdb"))

result = con.execute("""
    select review_id, order_id, review_creation_date
    from raw_reviews
    where review_id in (
        select review_id from raw_reviews group by review_id having count(*) > 1
    )
    order by review_id
    limit 20
""").df()

print(result)
