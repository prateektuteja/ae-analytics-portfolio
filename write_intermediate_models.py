"""
Writes intermediate-layer model SQL files for the ae_analytics_portfolio
dbt project (models/intermediate/).

Run from the dbt project root: ~/Projects/ae-analytics-portfolio/ae_analytics_portfolio/

Usage:
    python write_intermediate_models.py                # write all models
    python write_intermediate_models.py int_order_items # write just one
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models" / "intermediate"

MODELS = {
    "int_order_items_summary": """select
    order_id,
    count(*) as item_count,
    round(sum(price), 2) as total_item_value,
    round(sum(freight_value), 2) as total_freight_value
from {{ ref('stg_order_items') }}
group by order_id
""",
    "int_order_items": """select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_at,
    round(price, 2) as price,
    round(freight_value, 2) as freight_value
from {{ ref('stg_order_items') }}
""",
    "int_order_payments": """with payment_agg as (
    select
        order_id,
        round(sum(payment_value), 2) as total_paid_amount,
        sum(case when payment_type = 'credit_card' then payment_installments else 0 end) as payment_installments_count,
        count(case when payment_type = 'credit_card' then 1 end) as credit_card_count,
        count(distinct payment_type) as distinct_payment_types_count
    from {{ ref('stg_payments') }}
    group by order_id
)

select
    *,
    payment_installments_count > 1 as payment_installment_opted
from payment_agg
""",
    "int_order_reviews": """select
    md5(order_id || '~' || review_id) as order_review_id,
    order_id,
    review_id,
    review_score,
    review_created_at,
    review_answered_at
from {{ ref('stg_reviews') }}
""",
}


def write_model(name: str, overwrite_all: bool = False) -> None:
    if name not in MODELS:
        print(f"Unknown model: {name}. Available: {', '.join(MODELS)}")
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.sql"

    if path.exists() and not overwrite_all:
        answer = input(f"{path} already exists. Overwrite? [y/N] ").strip().lower()
        if answer != "y":
            print(f"Skipped {name}.")
            return

    path.write_text(MODELS[name])
    print(f"Wrote {path}")


def main():
    args = sys.argv[1:]
    targets = args if args else list(MODELS.keys())
    for name in targets:
        write_model(name)


if __name__ == "__main__":
    main()
