-- This file is for allocation audit, SRM demostration (Assumed allocation: 85% treatment / 15% control), and SMD of continuous features.

CREATE OR REPLACE VIEW criteo AS
SELECT * FROM read_parquet('data/processed/criteo_v2_1.parquet');

COPY (
    WITH counts AS (
        SELECT 
            treatment,
            COUNT(*) AS n
        FROM criteo
        GROUP BY treatment
    )

    SELECT 
        treatment,
        n,
        1.0 * n / SUM(n) OVER () AS allocation_rate
    FROM counts
) TO 'results/allocation_audit.csv' (HEADER, DELIMITER ',');

COPY (
    SELECT
        treatment,
        AVG(f0) AS f0_mean,
        VAR_SAMP(f0) AS f0_var,
        AVG(f2) AS f2_mean,
        VAR_SAMP(f2) AS f2_var,
        AVG(f7) AS f7_mean,
        VAR_SAMP(f7) AS f7_var,
        AVG(f10) AS f10_mean,
        VAR_SAMP(f10) AS f10_var
    FROM criteo
    GROUP BY treatment
    ORDER BY treatment
) TO 'results/covariate_balance_smd.csv' (HEADER, DELIMITER ',');

COPY (
    WITH source AS (
        SELECT
            treatment,
            f1, f3, f4, f5, f6, f8, f9, f11
        FROM criteo
    ),

    long_data AS (
        SELECT
            treatment,
            feature,
            feature_value AS category
        FROM source
        UNPIVOT (
            feature_value FOR feature
            IN (f1, f3, f4, f5, f6, f8, f9, f11)
        )
    ),

    counts AS (
        SELECT
            feature,
            treatment,
            category,
            COUNT(*) AS n
        FROM long_data
        GROUP BY feature, treatment, category
    ),

    shares AS (
        SELECT
            *,
            1.0 * n /
            SUM(n) OVER (
                PARTITION BY feature, treatment
            ) AS proportion
        FROM counts
    )

    SELECT
        feature,
        category,
        SUM(CASE WHEN treatment = 1
            THEN n ELSE 0 END) AS n_t,
        SUM(CASE WHEN treatment = 0
            THEN n ELSE 0 END) AS n_c,
        SUM(CASE WHEN treatment = 1
            THEN proportion ELSE 0 END) AS p_t,
        SUM(CASE WHEN treatment = 0
            THEN proportion ELSE 0 END) AS p_c
    FROM shares
    GROUP BY feature, category
    ORDER BY feature, category
) TO 'results/covariate_balance_proportion.csv' (HEADER, DELIMITER ',');