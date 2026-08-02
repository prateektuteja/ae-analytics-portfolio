
-- tests/assert_no_negative_payment_amounts.sql

-- Fails if any fct_orders row has a negative total_paid_amount.

select

    order_id,

    total_paid_amount

from {{ ref('fct_orders') }}

where total_paid_amount < 0

