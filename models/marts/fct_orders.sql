select
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
