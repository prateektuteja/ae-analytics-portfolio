with payment_agg as (
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
