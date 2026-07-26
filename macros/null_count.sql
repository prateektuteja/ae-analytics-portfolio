{% macro null_count(column_name) %}
    count(*) - count({{ column_name }})
{% endmacro %}
