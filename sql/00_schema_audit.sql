-- The aim of this file is to show that the structure of the data is complete before analysis.

CREATE OR REPLACE VIEW criteo AS
SELECT * FROM read_parquet('data/processed/criteo_v2_1.parquet');

WITH
expected_schema(column_name, expected_type) AS(
    VALUES
        ('f0', 'DOUBLE'),
        ('f1', 'DOUBLE'),
        ('f2', 'DOUBLE'),
        ('f3', 'DOUBLE'),
        ('f4', 'DOUBLE'),
        ('f5', 'DOUBLE'),
        ('f6', 'DOUBLE'),
        ('f7', 'DOUBLE'),
        ('f8', 'DOUBLE'),
        ('f9', 'DOUBLE'),
        ('f10', 'DOUBLE'),
        ('f11', 'DOUBLE'),
        ('treatment', 'BIGINT'),
        ('conversion', 'BIGINT'),
        ('visit', 'BIGINT'),
        ('exposure', 'BIGINT')
),

actual_schema AS (
    SELECT column_name, data_type AS actual_type
    FROM information_schema.columns
    WHERE table_schema = current_schema()
    AND table_name = 'criteo'
),

schema_mismatches AS (
    SELECT
        COALESCE(e.column_name, a.column_name) AS column_name,
        e.expected_type,
        a.actual_type
    FROM expected_schema e
    FULL JOIN actual_schema a
    ON e.column_name = a.column_name
    WHERE e.expected_type IS DISTINCT FROM a.actual_type
),

schema_check AS (
    SELECT
        COUNT(*) AS mismatch_count,
        COALESCE(
            STRING_AGG(
                column_name || ':actual=' || COALESCE(actual_type, 'MISSING')
                || ', expected=' || COALESCE(expected_type, 'UNEXPECTED'), '; '
                ORDER BY column_name
            ),
            'All16 columns match'
        ) AS detail
    FROM schema_mismatches
),

-- Compute some dataset-wide aggregates once rather than re-scanning the Parquet file
stats AS MATERIALIZED (
    SELECT
        COUNT(*) AS n,
        AVG(visit) AS visit_rate,
        AVG(conversion) AS conversion_rate,
        COUNT(*) FILTER (WHERE treatment IS NULL
                         OR treatment NOT IN (0, 1)) AS invalid_treatment,
        COUNT(*) FILTER (WHERE conversion IS NULL
                         OR conversion NOT IN (0, 1)) AS invalid_conversion,
        COUNT(*) FILTER (WHERE visit IS NULL
                         OR visit NOT IN (0, 1)) AS invalid_visit,
        COUNT(*) FILTER (WHERE exposure IS NULL
                         OR exposure NOT IN (0, 1)) AS invalid_exposure,
        COUNT(*) FILTER (WHERE f0 IS NULL) AS null_f0,
        COUNT(*) FILTER (WHERE f1 IS NULL) AS null_f1,
        COUNT(*) FILTER (WHERE f2 IS NULL) AS null_f2,
        COUNT(*) FILTER (WHERE f3 IS NULL) AS null_f3,
        COUNT(*) FILTER (WHERE f4 IS NULL) AS null_f4,
        COUNT(*) FILTER (WHERE f5 IS NULL) AS null_f5,
        COUNT(*) FILTER (WHERE f6 IS NULL) AS null_f6,
        COUNT(*) FILTER (WHERE f7 IS NULL) AS null_f7,
        COUNT(*) FILTER (WHERE f8 IS NULL) AS null_f8,
        COUNT(*) FILTER (WHERE f9 IS NULL) AS null_f9,
        COUNT(*) FILTER (WHERE f10 IS NULL) AS null_f10,
        COUNT(*) FILTER (WHERE f11 IS NULL) AS null_f11,
        COUNT(*) FILTER (WHERE treatment IS NULL) AS null_treatment,
        COUNT(*) FILTER (WHERE conversion IS NULL) AS null_conversion,
        COUNT(*) FILTER (WHERE visit IS NULL) AS null_visit,
        COUNT(*) FILTER (WHERE exposure IS NULL) AS null_exposure,
        COUNT(*) FILTER (WHERE ISNAN(f0)
                         OR ISINF(f0)) AS nonfinite_f0,
        COUNT(*) FILTER (WHERE ISNAN(f1)
                         OR ISINF(f1)) AS nonfinite_f1,
        COUNT(*) FILTER (WHERE ISNAN(f2)
                         OR ISINF(f2)) AS nonfinite_f2,
        COUNT(*) FILTER (WHERE ISNAN(f3)
                         OR ISINF(f3)) AS nonfinite_f3,
        COUNT(*) FILTER (WHERE ISNAN(f4)
                         OR ISINF(f4)) AS nonfinite_f4,
        COUNT(*) FILTER (WHERE ISNAN(f5)
                         OR ISINF(f5)) AS nonfinite_f5,
        COUNT(*) FILTER (WHERE ISNAN(f6)
                         OR ISINF(f6)) AS nonfinite_f6,
        COUNT(*) FILTER (WHERE ISNAN(f7)
                         OR ISINF(f7)) AS nonfinite_f7,
        COUNT(*) FILTER (WHERE ISNAN(f8)
                         OR ISINF(f8)) AS nonfinite_f8,
        COUNT(*) FILTER (WHERE ISNAN(f9)
                         OR ISINF(f9)) AS nonfinite_f9,
        COUNT(*) FILTER (WHERE ISNAN(f10)
                         OR ISINF(f10)) AS nonfinite_f10,
        COUNT(*) FILTER (WHERE ISNAN(f11)
                         OR ISINF(f11)) AS nonfinite_f11,
        MIN(f0) AS min_f0,
        MAX(f0) AS max_f0,
        AVG(f0) AS mean_f0,
        APPROX_COUNT_DISTINCT(f0) AS approx_distinct_f0,
        MIN(f1) AS min_f1,
        MAX(f1) AS max_f1,
        AVG(f1) AS mean_f1,
        APPROX_COUNT_DISTINCT(f1) AS approx_distinct_f1,
        MIN(f2) AS min_f2,
        MAX(f2) AS max_f2,
        AVG(f2) AS mean_f2,
        APPROX_COUNT_DISTINCT(f2) AS approx_distinct_f2,
        MIN(f3) AS min_f3,
        MAX(f3) AS max_f3,
        AVG(f3) AS mean_f3,
        APPROX_COUNT_DISTINCT(f3) AS approx_distinct_f3,
        MIN(f4) AS min_f4,
        MAX(f4) AS max_f4,
        AVG(f4) AS mean_f4,
        APPROX_COUNT_DISTINCT(f4) AS approx_distinct_f4,
        MIN(f5) AS min_f5,
        MAX(f5) AS max_f5,
        AVG(f5) AS mean_f5,
        APPROX_COUNT_DISTINCT(f5) AS approx_distinct_f5,
        MIN(f6) AS min_f6,
        MAX(f6) AS max_f6,
        AVG(f6) AS mean_f6,
        APPROX_COUNT_DISTINCT(f6) AS approx_distinct_f6,
        MIN(f7) AS min_f7,
        MAX(f7) AS max_f7,
        AVG(f7) AS mean_f7,
        APPROX_COUNT_DISTINCT(f7) AS approx_distinct_f7,
        MIN(f8) AS min_f8,
        MAX(f8) AS max_f8,
        AVG(f8) AS mean_f8,
        APPROX_COUNT_DISTINCT(f8) AS approx_distinct_f8,
        MIN(f9) AS min_f9,
        MAX(f9) AS max_f9,
        AVG(f9) AS mean_f9,
        APPROX_COUNT_DISTINCT(f9) AS approx_distinct_f9,
        MIN(f10) AS min_f10,
        MAX(f10) AS max_f10,
        AVG(f10) AS mean_f10,
        APPROX_COUNT_DISTINCT(f10) AS approx_distinct_f10,
        MIN(f11) AS min_f11,
        MAX(f11) AS max_f11,
        AVG(f11) AS mean_f11,
        APPROX_COUNT_DISTINCT(f11) AS approx_distinct_f11,
        COUNT(*) FILTER (WHERE treatment = 0 AND exposure = 0) AS t0e0,
        COUNT(*) FILTER (WHERE treatment = 0 AND exposure = 1) AS t0e1,
        COUNT(*) FILTER (WHERE treatment = 1 AND exposure = 0) AS t1e0,
        COUNT(*) FILTER (WHERE treatment = 1 AND exposure = 1) AS t1e1,
        COUNT(*) FILTER (WHERE conversion = 0 AND visit = 0) AS c0v0,
        COUNT(*) FILTER (WHERE conversion = 0 AND visit = 1) AS c0v1,
        COUNT(*) FILTER (WHERE conversion = 1 AND visit = 0) AS c1v0,
        COUNT(*) FILTER (WHERE conversion = 1 AND visit = 1) AS c1v1
    FROM criteo
),
checks AS (
    SELECT 'row_count' AS check_name,
       n::VARCHAR AS observed,
       13979592 AS expected,
       n = 13979592 AS passed
    FROM stats

    UNION ALL

    SELECT 'schema_columns_types',
        detail,
        'All 16 columns match',
        mismatch_count = 0
    FROM schema_check

    UNION ALL

    SELECT
        'binary_treatment',
        invalid_treatment::VARCHAR,
        '0 invalid rows',
        invalid_treatment = 0
    FROM stats

    UNION ALL

    SELECT
        'binary_conversion',
        invalid_conversion::VARCHAR,
        '0 invalid rows',
        invalid_conversion = 0
    FROM stats
    
    UNION ALL

    SELECT
        'binary_visit',
        invalid_visit::VARCHAR,
        '0 invalid rows',
        invalid_visit = 0
    FROM stats
    
    UNION ALL

    SELECT
        'binary_exposure',
        invalid_exposure::VARCHAR,
        '0 invalid rows',
        invalid_exposure = 0
    FROM stats

    UNION ALL

    SELECT
        'null_f0',
        null_f0::VARCHAR,
        '0',
        null_f0 = 0
    FROM stats

    UNION ALL

    SELECT
        'null_f1',
        null_f1::VARCHAR,
        '0',
        null_f1 = 0
    FROM stats

    UNION ALL

    SELECT
        'null_f2',
        null_f2::VARCHAR,
        '0',
        null_f2 = 0
    FROM stats

    UNION ALL

    SELECT
        'null_f3',
        null_f3::VARCHAR,
        '0',
        null_f3 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f4',
        null_f4::VARCHAR,
        '0',
        null_f4 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f5',
        null_f5::VARCHAR,
        '0',
        null_f5 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f6',
        null_f6::VARCHAR,
        '0',
        null_f6 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f7',
        null_f7::VARCHAR,
        '0',
        null_f7 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f8',
        null_f8::VARCHAR,
        '0',
        null_f8 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f9',
        null_f9::VARCHAR,
        '0',
        null_f9 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'null_f10',
        null_f10::VARCHAR,
        '0',
        null_f10 = 0
    FROM stats

    UNION ALL

    SELECT
        'null_f11',
        null_f11::VARCHAR,
        '0',
        null_f11 = 0
    FROM stats

    UNION ALL

    SELECT
        'null_treatment',
        null_treatment::VARCHAR,
        '0',
        null_treatment = 0
    FROM stats

    UNION ALL

    SELECT
        'null_conversion',
        null_conversion::VARCHAR,
        '0',
        null_conversion = 0
    FROM stats

    UNION ALL

    SELECT
        'null_visit',
        null_visit::VARCHAR,
        '0',
        null_visit = 0
    FROM stats

    UNION ALL

    SELECT
        'null_exposure',
        null_exposure::VARCHAR,
        '0',
        null_exposure = 0
    FROM stats

    UNION

    SELECT
        'nonfinite_f0',
        nonfinite_f0::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f0 = 0
    FROM stats
    
    UNION ALL

    SELECT
        'nonfinite_f1',
        nonfinite_f1::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f1 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f2',
        nonfinite_f2::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f2 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f3',
        nonfinite_f3::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f3 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f4',
        nonfinite_f4::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f4 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f5',
        nonfinite_f5::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f5 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f6',
        nonfinite_f6::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f6 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f7',
        nonfinite_f7::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f7 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f8',
        nonfinite_f8::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f8 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f9',
        nonfinite_f9::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f9 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f10',
        nonfinite_f10::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f10 = 0
    FROM stats

    UNION ALL

    SELECT
        'nonfinite_f11',
        nonfinite_f11::VARCHAR,
        '0 (NaN or +/-Inf)',
        nonfinite_f11 = 0
    FROM stats

    UNION ALL

    SELECT
        'visit_rate',
        ROUND(100 * visit_rate, 6)::VARCHAR || '%',
        '4.6992% +/- 0.05 percentage points',
        COALESCE(ABS(visit_rate - 0.046992) <= 0.0005, FALSE)
    FROM stats

    UNION ALL

    SELECT
        'conversion_rate',
        ROUND(100 * conversion_rate, 6)::VARCHAR || '%',
        '0.292% +/- 0.01 percentage points',
        COALESCE(ABS(conversion_rate - 0.00292) <= 0.0001, FALSE)
    FROM stats

    UNION ALL

    SELECT
        'treatment_x_exposure',
        'T0E1=' || T0E1::VARCHAR,
        'T0E1 is 0',
        T0E1 = 0
    FROM stats

    UNION ALL

    SELECT
        'conversion_x_visit',
        'C1V0=' || C1V0::VARCHAR,
        'C1V0 is 0',
        C1V0 = 0
    FROM stats

    UNION ALL

    SELECT
        'feature_f0',
        'min=' || COALESCE(ROUND(min_f0, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f0, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f0, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f0::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f1',
        'min=' || COALESCE(ROUND(min_f1, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f1, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f1, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f1::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f2',
        'min=' || COALESCE(ROUND(min_f2, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f2, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f2, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f2::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f3',
        'min=' || COALESCE(ROUND(min_f3, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f3, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f3, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f3::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f4',
        'min=' || COALESCE(ROUND(min_f4, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f4, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f4, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f4::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f5',
        'min=' || COALESCE(ROUND(min_f5, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f5, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f5, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f5::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f6',
        'min=' || COALESCE(ROUND(min_f6, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f6, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f6, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f6::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f7',
        'min=' || COALESCE(ROUND(min_f7, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f7, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f7, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f7::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f8',
        'min=' || COALESCE(ROUND(min_f8, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f8, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f8, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f8::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f9',
        'min=' || COALESCE(ROUND(min_f9, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f9, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f9, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f9::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f10',
        'min=' || COALESCE(ROUND(min_f10, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f10, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f10, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f10::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats

    UNION ALL

    SELECT
        'feature_f11',
        'min=' || COALESCE(ROUND(min_f11, 6)::VARCHAR, 'NULL')
          || '; max=' || COALESCE(ROUND(max_f11, 6)::VARCHAR, 'NULL')
          || '; mean=' || COALESCE(ROUND(mean_f11, 6)::VARCHAR, 'NULL')
          || '; approx_distinct=' || approx_distinct_f11::VARCHAR,
        'informational',
        NULL::BOOLEAN
    FROM stats
)
SELECT * 
FROM checks
;