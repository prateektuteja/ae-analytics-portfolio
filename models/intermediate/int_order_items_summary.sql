select
    order_id,
    count(*) as item_count,
    round(sum(price), 2) as total_item_value,
    round(sum(freight_value), 2) as total_freight_value
from {{ ref('stg_order_items') }}
group by order_id
