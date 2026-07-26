with source as (
    select * from {{ source('olist', 'raw_payments') }}
)

select
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    cast(payment_value as double) as payment_value
from source
