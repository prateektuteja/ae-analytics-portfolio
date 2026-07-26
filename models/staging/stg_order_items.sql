with source as (
    select * from {{ source('olist', 'raw_order_items') }}
)

select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    cast(shipping_limit_date as timestamp) as shipping_limit_at,
    cast(price as double) as price,
    cast(freight_value as double) as freight_value
from source
