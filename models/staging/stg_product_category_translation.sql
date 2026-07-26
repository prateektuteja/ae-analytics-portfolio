with source as (
    select * from {{ source('olist', 'raw_product_category_translation') }}
)

select
    product_category_name,
    product_category_name_english
from source
