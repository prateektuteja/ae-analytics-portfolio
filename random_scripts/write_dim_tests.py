"""
Appends unique/not_null tests for dim_customers, dim_sellers, dim_products
to models/marts/marts_model.yml.

These three dims are pure pass-throughs from staging, but dbt tests don't
propagate across models -- testing stg_customers.customer_id doesn't test
dim_customers.customer_id, since they're separate models. This adds the
standing PK guarantee (unique + not_null) directly on the mart layer.

Since `models:` in the yml is a YAML sequence, these new entries are appended
as additional list items at the end of the file -- no need to repeat the
top-level `models:` key (that would silently overwrite the existing
fct_orders/fct_order_items blocks instead of merging with them).

Run this from the dbt project root:
    ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/
"""

from pathlib import Path

PATH = Path("models/marts/marts_model.yml")

NEW_BLOCKS = """
  - name: dim_customers

    columns:

      - name: customer_id

        tests:

          - unique

          - not_null

  - name: dim_sellers

    columns:

      - name: seller_id

        tests:

          - unique

          - not_null

  - name: dim_products

    columns:

      - name: product_id

        tests:

          - unique

          - not_null
"""


def main():
    if not PATH.exists():
        raise SystemExit(f"{PATH} not found -- run this from the dbt project root")

    content = PATH.read_text()

    if "name: dim_customers" in content:
        print("dim_customers block already present -- skipping to avoid duplicates")
        return

    content = content.rstrip("\n") + "\n" + NEW_BLOCKS
    PATH.write_text(content)
    print(f"Appended dim_customers/dim_sellers/dim_products test blocks to {PATH}")


if __name__ == "__main__":
    main()
