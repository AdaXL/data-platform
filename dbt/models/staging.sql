-- This file contains SQL for staging models in dbt.

WITH source_data AS (
    SELECT
        id,
        name,
        created_at,
        updated_at
    FROM
        raw_data_table
)

SELECT
    id,
    name,
    created_at,
    updated_at
FROM
    source_data;
