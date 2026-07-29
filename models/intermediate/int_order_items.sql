select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_at,
    round(price, 2) as price,
    round(freight_value, 2) as freight_value
from {{ ref('stg_order_items') }}
