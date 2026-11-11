-- This file is the start of all the following analysis, so-called "sufficient statistics".

CREATE OR REPLACE VIEW criteo AS
SELECT * FROM read_parquet('data/processed/criteo_v2_1.parquet');

COPY (
  SELECT treatment,
         COUNT(*)                          AS n,
         SUM(visit)                        AS n_visit,
         SUM(conversion)                   AS n_conversion,
         SUM(exposure)                     AS n_exposure,
         SUM(visit)::DOUBLE / COUNT(*)      AS visit_rate,
         SUM(conversion)::DOUBLE / COUNT(*) AS conversion_rate,
         SUM(exposure)::DOUBLE / COUNT(*)   AS exposure_rate
  FROM criteo
  GROUP BY treatment
  ORDER BY treatment
) TO 'results/arm_summary.csv' (HEADER, DELIMITER ',');

COPY (
  SELECT treatment, exposure, visit, conversion, COUNT(*) AS n
  FROM criteo
  GROUP BY treatment, exposure, visit, conversion
  ORDER BY treatment, exposure, visit, conversion
) TO 'results/cell_counts.csv' (HEADER, DELIMITER ',');