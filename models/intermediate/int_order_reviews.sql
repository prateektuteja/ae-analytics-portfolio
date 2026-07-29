select
    md5(order_id || '~' || review_id) as order_review_id,
    order_id,
    review_id,
    review_score,
    review_created_at,
    review_answered_at
from {{ ref('stg_reviews') }}
