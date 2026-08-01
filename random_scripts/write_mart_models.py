"""
Writes the Day 6 mart models to models/marts/.

Same pattern as write_intermediate_models.py (Day 5): a MODELS dict holding
each model's SQL, write_model() to write one, main() to write all (or a
subset passed as CLI args).

Run this from the dbt project root:
    ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/

Usage:
    python write_mart_models.py                                  # writes all 4
    python write_mart_models.py dim_customers dim_sellers         # writes a subset
"""

import sys
from pathlib import Path

MARTS_DIR = Path("models/marts")

MODELS = {
    "dim_customers": """select
    customer_id,
    customer_unique_id,
    customer_city,
    customer_state,
    customer_zip_code_prefix
from {{ ref('stg_customers') }}
""",

    "dim_sellers": """select
    seller_id,
    seller_city,
    seller_state,
    seller_zip_code_prefix
from {{ ref('stg_sellers') }}
""",

    "dim_products": """select
    p.product_id,
    coalesce(t.product_category_name_english, p.product_category_name) as product_category_name,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm,
    p.product_photos_qty
from {{ ref('stg_products') }} p
left join {{ ref('stg_product_category_translation') }} t
    on p.product_category_name = t.product_category_name
""",

    "fct_orders": """select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_at,
    o.order_approved_at,
    o.order_delivered_carrier_at,
    o.order_delivered_customer_at,
    o.order_estimated_delivery_at,
    i.item_count,
    i.total_item_value,
    i.total_freight_value,
    p.total_paid_amount,
    p.payment_installments_count,
    p.credit_card_count,
    p.payment_installment_opted,
    p.distinct_payment_types_count
from {{ ref('stg_orders') }} o
left join {{ ref('int_order_items_summary') }} i on o.order_id = i.order_id
left join {{ ref('int_order_payments') }} p on o.order_id = p.order_id
""",
}


def write_model(name: str) -> None:
    if name not in MODELS:
        print(f"Unknown model: {name} (known: {', '.join(MODELS)})")
        return
    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    path = MARTS_DIR / f"{name}.sql"
    path.write_text(MODELS[name])
    print(f"Wrote {path}")


def main() -> None:
    names = sys.argv[1:] if len(sys.argv) > 1 else list(MODELS)
    for name in names:
        write_model(name)


if __name__ == "__main__":
    main()
