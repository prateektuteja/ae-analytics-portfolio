
-- tests/assert_no_orphaned_order_items.sql

-- Fails if any fct_order_items row references an order_id not present in fct_orders.

select

    oi.order_id,

    oi.order_item_id

from {{ ref('fct_order_items') }} oi

left join {{ ref('fct_orders') }} o

    on oi.order_id = o.order_id

where o.order_id is null

