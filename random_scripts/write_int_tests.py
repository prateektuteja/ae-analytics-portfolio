"""
Creates models/intermediate/int_models.yml with schema tests for the 4
intermediate models built on Day 5 (int_order_items_summary, int_order_items,
int_order_payments, int_order_reviews).

PK reasoning (from Day 5 spec / build):
  - int_order_items_summary: order grain -> order_id is a single-column PK
  - int_order_payments:      order grain -> order_id is a single-column PK
  - int_order_reviews:       native (order_id, review_id) grain, but has a
                              surrogate key (order_review_id = md5(order_id
                              || '~' || review_id)) -> single-column PK
  - int_order_items:         true composite grain (order_id + order_item_id),
                              no surrogate key added -> full uniqueness test
                              needs dbt_utils.unique_combination_of_columns,
                              deferred to Day 8. not_null on both key columns
                              added now as a safe partial check.

This is the FIRST schema.yml for the intermediate layer (creates the file
fresh -- staging already has stg_models.yml, marts already has
marts_model.yml, intermediate had none yet).

Run this from the dbt project root:
    ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/
"""

from pathlib import Path

PATH = Path("models/intermediate/int_models.yml")

CONTENT = """models:

  - name: int_order_items_summary

    columns:

      - name: order_id

        tests:

          - unique

          - not_null

  - name: int_order_payments

    columns:

      - name: order_id

        tests:

          - unique

          - not_null

  - name: int_order_reviews

    columns:

      - name: order_review_id

        tests:

          - unique

          - not_null

  - name: int_order_items

    columns:

      - name: order_id

        tests:

          - not_null

      - name: order_item_id

        tests:

          - not_null

    # Composite uniqueness (order_id + order_item_id) deferred to Day 8 --
    # needs dbt_utils.unique_combination_of_columns, not installed yet.
"""


def main():
    if PATH.exists():
        print(f"{PATH} already exists -- not overwriting. Delete it first if you want a clean rewrite.")
        return

    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(CONTENT)
    print(f"Created {PATH}")


if __name__ == "__main__":
    main()
