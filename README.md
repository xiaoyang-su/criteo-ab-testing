# Criteo Advertising Incrementality: An A/B Testing Portfolio

This data science portfolio develops a reproducible, retrospective analysis of
Criteo's corrected Uplift v2.1 benchmark, reported to contain 13,979,592 user-level
records from randomized advertising incrementality tests. The central question
is whether advertising eligibility increased website visits relative to holdout
assignment, with conversions as a secondary business outcome.

The analysis uses `treatment` for assignment-based comparisons. Actual
advertising `exposure` occurs after assignment. The released data were subsampled
and anonymized, so estimates are interpreted within the benchmark
setting rather than as the original campaigns' incrementality or measured ROI.

**Status:** Data download, SHA256 verification, Gzip CSV-to-Parquet conversion,
DuckDB connections, SQL-file execution, schema auditing, experiment-metric
aggregation, allocation auditing, and covariate-balance diagnostics are
implemented. The local raw archive and generated Parquet both
have entries in `data/CHECKSUMS.txt`. The committed audit confirms 13,979,592 rows,
the expected 16-column schema, and passing data-integrity checks. Arm summaries
and joint cell counts, allocation counts, and covariate summaries are saved under
`results/`. The completed [validation notebook](notebooks/01_validation.ipynb)
includes an illustrative SRM assessment, balance diagnostics, a categorical
balance chart, and a validation summary. The completed
[ITT inference notebook](notebooks/02_itt_inference.ipynb) adds absolute and
relative lift, two-proportion z-tests, 95% confidence intervals, and binomial
bootstrap checks for visits and conversions. Both notebooks use labeled English
output with consistent numeric formatting. Power/MDE and variance reduction
remain pending.

See the [data card](DATA_CARD.md) for source, fields, limitations, licensing, and
citations, and the [analysis plan](ANALYSIS_PLAN.md) for the planned methodology.

## Local setup and data preparation

Use Python 3.10 or later in the Conda environment `abtest`. Run these commands
from the project root in PowerShell:

```powershell
conda activate abtest
python -m pip install -r requirements.txt
python -m src.download_data
python -m src.checksums
python -m src.prepare_data
```

If the environment is already provisioned, the dependency installation step can
be skipped. Without activating the environment, prefix module commands with
`conda run --no-capture-output -n abtest`, for example:

```powershell
conda run --no-capture-output -n abtest python -m src.prepare_data
```

The preparation workflow is:

```text
Official .csv.gz archive
    -> verify the official SHA256 and record the raw file checksum
    -> read the compressed CSV directly through DuckDB
    -> write ZSTD-compressed Parquet and record its checksum
    -> verify the Parquet before executing user-written SQL
```

The downloader streams the archive from the
[official Criteo mirror](https://huggingface.co/datasets/criteo/criteo-uplift/blob/main/criteo-research-uplift-v2.1.csv.gz)
to `data/raw/criteo-research-uplift-v2.1.csv.gz`. Network failures are retried up to
three times, restarting the transfer. A downloaded file is accepted only after
its SHA256 matches the official value; failed transfers clean up their `.part`
file. An existing valid archive is verified and reused.

`prepare_data.py` calls the shared DuckDB connection helper, reads the Gzip CSV
without creating a separate uncompressed CSV, and writes
`data/processed/criteo_v2_1.parquet`. DuckDB infers the CSV types; the conversion
preserves the source columns and adds no `row_id`. Conversion is separate from
analysis and does not load the full dataset into pandas.

Repeating preparation verifies an existing Parquet and skips conversion. A
missing checksum, mismatched file, or missing Parquet with an existing checksum
record causes an error rather than silently replacing the integrity baseline.

## Running SQL files

The implemented SQL files in `sql/` audit the dataset, summarize allocation and
covariates, and aggregate experiment metrics. You can also add your own SQL; the
runner rejects an empty file. Each run
verifies the Parquet and registers it as the session view **`criteo`**, which your SQL can query.
Each run uses a new DuckDB connection; a separate database server is unnecessary.

To choose a SQL file from a numbered menu:

```powershell
python -m src.run_sql
```

The menu lists `.sql` files under `sql/`, including subdirectories. Enter a file
number to execute it or `q` to cancel. In VS Code, select the `abtest` Python
interpreter, open `src/run_sql.py`, and use **Run Python File in Terminal** to
open the same menu. Direct execution is also supported:

```powershell
python src/run_sql.py
```

To specify a file directly, replace `your_query.sql` with a file you have written:

```powershell
python -m src.run_sql sql/your_query.sql
python -m src.run_sql sql/your_query.sql --preview-rows 50
python -m src.run_sql sql/your_query.sql --output results/your_result.csv
```

All statements in the file execute. The runner displays only the final
statement's result, with a default preview of 20 rows. `--output` streams the
complete final result to CSV in batches of 10,000 rows, including a header, and
refuses to overwrite an existing output. Paths supplied to the runner, including
relative paths inside SQL, are resolved from the project root.

### Schema audit and experiment aggregates

Run the schema audit to preview its checks:

```powershell
python -m src.run_sql sql/00_schema_audit.sql --preview-rows 50
```

The audit checks row count, column names and types, binary-field validity,
missing values, non-finite feature values, overall outcome rates, and the
constraints that control users have no exposure and conversions imply visits.
It also reports feature ranges, means, and approximate distinct counts as
informational rows, with no pass/fail value. Means of encoded categorical
features are descriptive numeric summaries, not covariate-balance evidence.
The committed output is `results/schema_audit.csv`; all 38 pass/fail checks pass,
alongside 12 informational feature summaries. These checks establish data
integrity, not treatment randomization or statistical significance.

To export a fresh audit, choose a new output path because the runner refuses to
overwrite an existing `--output` file:

```powershell
python -m src.run_sql sql/00_schema_audit.sql --output results/schema_audit_rerun.csv
```

Generate the experiment aggregates with:

```powershell
python -m src.run_sql sql/02_experiment_metrics.sql
```

This SQL file uses two `COPY` statements to write its outputs directly:

| Output | Contents |
| --- | --- |
| `results/arm_summary.csv` | Sample size, visit/conversion/exposure counts, and corresponding rates by `treatment` |
| `results/cell_counts.csv` | Counts for observed combinations of `treatment`, `exposure`, `visit`, and `conversion` |

Run this file without `--output`: both CSV destinations are already specified
inside the SQL. Re-running it overwrites those two CSVs through DuckDB's `COPY`;
the runner's refusal to overwrite applies only to its own `--output` export.
The final console result is the last `COPY` statement's status, not the contents
of both exported tables.

The committed arm summary contains these descriptive results:

| Assignment | Users | Visits | Conversions | Visit rate | Conversion rate | Exposure rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Control (`treatment=0`) | 2,096,937 | 80,105 | 4,063 | 3.820096% | 0.193759% | 0% |
| Treatment (`treatment=1`) | 11,882,655 | 576,824 | 36,711 | 4.854336% | 0.308946% | 3.603673% |

These aggregate counts feed the completed unadjusted ITT analysis in
`notebooks/02_itt_inference.ipynb`. Power/MDE and covariate adjustment remain
planned work; covariate adjustment requires additional feature-level data.

The standalone DuckDB CLI is another optional way to explore data interactively.
It runs independently of these Python scripts and does not automatically apply
the project's checksum verification, connection settings, or `criteo` view.

## Experiment validation

Generate the allocation and covariate summaries from the verified Parquet:

```powershell
python -m src.run_sql sql/01_randomization.sql
```

The SQL exports three aggregate tables directly through `COPY`:

| Output | Contents |
| --- | --- |
| `results/allocation_audit.csv` | Sample size and allocation share by `treatment` |
| `results/covariate_balance_smd.csv` | Within-arm means and sample variances for continuous features `f0`, `f2`, `f7`, and `f10` |
| `results/covariate_balance_proportion.csv` | Category-level counts and within-arm proportions for the eight encoded categorical features |

Run this SQL without `--output`; its destinations are defined in the file.
Re-running it overwrites these three CSVs. The final console result reports the
last `COPY` status, rather than displaying the diagnostic tables. The SQL
prepares the inputs; SMDs, SRM tests, TVD, and maximum category-proportion
differences are calculated in the notebook.

Open [01_validation.ipynb](notebooks/01_validation.ipynb) with the `abtest` kernel
and run its cells in order. First generate `arm_summary.csv` and `cell_counts.csv`
with `sql/02_experiment_metrics.sql`, as described above. The notebook re-runs the
schema audit and `sql/01_randomization.sql`, then reads the aggregate CSVs. Its
setup cell currently contains a local absolute project path; adapt `root` to
your checkout. The setup changes the working directory and adds that root to
the kernel's Python import path before importing `src.run_sql`.

The committed notebook reports:

| Diagnostic | Result | Interpretation |
| --- | --- | --- |
| Allocation | 11,882,655 treatment and 2,096,937 control observations; treatment share 85.000013% | Consistent with an approximately 85%/15% split |
| Illustrative SRM | Pearson chi-squared p = 0.998924; two-sided exact binomial p = 0.999402 | No mismatch detected when the expected treatment probability is assumed to be exactly 0.85 |
| Continuous covariates | All four absolute SMDs below 0.022; maximum 0.021270 for `f7` | Small mean differences relative to the notebook's descriptive 0.10 reference |
| Categorical covariates | TVD ranges from 0.000966 (`f11`) to 0.013841 (`f3`); largest category gap is 1.379447 percentage points for `f3` | Small absolute marginal differences; no categorical pass/fail cutoff is specified |

The categorical balance chart ranks all eight features by TVD in a horizontal
bar chart with value labels. The validation summary combines these diagnostics
with the 38 passing integrity checks and supports proceeding to ITT estimation
for the released sample.

The exact expected assignment probability for the released sample is unavailable,
so the SRM results are assumption-dependent and do not establish a definitive
formal SRM pass. Marginal covariate balance does not prove randomization or
establish joint-distribution balance; treatment-assignment predictability has
not been assessed. Missing user IDs, experiment IDs, and timestamps limit further
validation, while non-uniform negative-label sampling limits generalization to
the original advertising populations. The ITT inference notebook compares the
full assigned arms using `treatment`, with `visit` as the primary outcome and
`conversion` as the secondary outcome.

## ITT inference

Open [02_itt_inference.ipynb](notebooks/02_itt_inference.ipynb) with the `abtest`
kernel after reviewing Notebook 01's validation report. Adapt the setup cell's
`root` path to your checkout and run the cells in order. The notebook runs
`sql/02_experiment_metrics.sql`, overwriting its two aggregate CSV outputs, then
reads `results/arm_summary.csv`. Inference results are displayed and retained in
the notebook; it does not export a separate inference-results CSV.

The implemented analysis includes:

- Absolute differences in assigned-arm outcome proportions and relative lift
  against the control rate, retaining all observations in each assigned arm.
- Two-sided, pooled two-proportion z-tests for equality of outcome rates.
- Newcombe 95% confidence intervals for absolute differences, using the
  installed statsmodels default for `compare="diff"`.
- Aggregate binomial bootstrap checks with fixed arm sizes, 99,999 replicates,
  percentile intervals, and bootstrap standard errors.

The committed results are:

| Measure | Visit (primary) | Conversion (secondary) |
| --- | ---: | ---: |
| Absolute lift (percentage points) | +1.034240 | +0.115187 |
| Relative lift | +27.073676% | +59.448812% |
| z-statistic | 65.247430 | 28.516529 |
| Two-sided p-value | Numerical underflow; reported as `0.0` | 7.308263e-179 |
| Analytical 95% CI (percentage points) | [1.005492, 1.062848] | [0.108377, 0.121852] |
| Bootstrap percentile 95% CI (percentage points) | [1.005523, 1.062876] | [0.108421, 0.121954] |

Both outcome-specific tests reject equal rates at the 5% reference level, and
both analytical intervals exclude zero. The visit p-value is too small for the
calculation to represent as a positive floating-point value; `0.0` is not a
mathematically zero probability. Absolute lift is expressed in percentage
points, while relative lift is a percentage increase against the control rate.
The notebook calculates intervals for absolute lift only, with no multiplicity
adjustment across outcomes.

The bootstrap intervals closely match the analytical intervals under the shared
independent-binomial assumptions. The generator is initialized with seed 42 in
the visit bootstrap cell and reused for conversion; reset it and run both cells
in sequence for reproducibility. Saved bootstrap summaries reflect the recorded
execution history, so a fresh sequential run may differ slightly.

These positive, precisely estimated contrasts describe the released benchmark.
The bootstrap does not resolve dependence between observations, pooled-experiment
heterogeneity, or non-uniform release sampling. The analysis supplies an
unadjusted reference for subsequent power/MDE and covariate-adjustment work;
it does not by itself establish original-campaign incrementality or profitability.

## Project structure

```text
Project/
|-- README.md
|-- DATA_CARD.md                    # Dataset provenance and limitations
|-- ANALYSIS_PLAN.md                # Planned statistical work
|-- requirements.txt
|-- pytest.ini
|-- src/
|   |-- __init__.py
|   |-- download_data.py            # Official archive download and verification
|   |-- checksums.py                # SHA256 calculation and manifest management
|   |-- db.py                       # DuckDB connection factory
|   |-- data.py                     # Shared paths, verification, and view setup
|   |-- prepare_data.py             # Verified Gzip CSV-to-Parquet conversion
|   `-- run_sql.py                  # SQL selection, execution, preview, and export
|-- sql/
|   |-- 00_schema_audit.sql          # Schema, integrity, and feature summaries
|   |-- 01_randomization.sql         # Export allocation and covariate summaries
|   `-- 02_experiment_metrics.sql    # Export arm metrics and joint cell counts
|-- tests/
|   |-- test_checksums.py
|   |-- test_download.py
|   `-- test_db.py
|-- data/
|   |-- CHECKSUMS.txt                # Tracked integrity records
|   |-- raw/                        # Downloaded archive; ignored by Git
|   |-- processed/                  # Generated Parquet; ignored by Git
|   `-- tmp/                        # DuckDB spill directory; generated as needed
|-- results/                        # Aggregate query outputs committed to Git
|   |-- schema_audit.csv            # Data-integrity checks and feature summaries
|   |-- arm_summary.csv             # Counts and rates by treatment assignment
|   |-- cell_counts.csv             # Joint assignment/exposure/outcome counts
|   |-- allocation_audit.csv        # Assignment counts and allocation shares
|   |-- covariate_balance_smd.csv    # Continuous-feature means and variances
|   `-- covariate_balance_proportion.csv # Category counts and proportions
|-- notebooks/
|   |-- 01_validation.ipynb          # Integrity, allocation, SRM, and balance report
|   `-- 02_itt_inference.ipynb       # Lift, z-tests, confidence intervals, and bootstrap
`-- dashboard/                      # Reserved for subsequent presentation
```

`data.py` contains shared data-access helpers; it does not generate synthetic
data. `db.py` only creates connections. Data verification and Parquet view
registration are performed by the pipeline helpers.

## Integrity, storage, and connection settings

The expected SHA256 of the official compressed archive is pinned in
`src/checksums.py`:

```text
2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc
```

`data/CHECKSUMS.txt` records separate hashes for the raw archive and generated
Parquet. The Parquet checksum is a project-generated integrity record, not an
official Criteo checksum. The standalone `python -m src.checksums` command
verifies the **raw archive only**, against both the official hash and its manifest
entry. Parquet verification happens when preparation is repeated and before
the SQL runner registers the data view. Hash verification establishes file
integrity; schema and analytical validity require the subsequent audits.

The default DuckDB connection is in-memory, with a `4GB` DuckDB memory limit and
one thread. The pipeline configures spill storage under `data/tmp/`. DuckDB's
memory limit does not cap the entire Python process. For notebooks or other
Python scripts, the same connection factory is available:

```python
from src.db import connect_database

with connect_database() as connection:
    # Add your own queries here.
    pass
```

`connect_database()` also accepts `memory_limit`, `threads`, and an optional
database file path. Relative database paths resolve from the project root;
parent directories must already exist. Keep any database containing row-level
data under `data/` so it remains ignored by Git.

Raw, extracted, and processed row-level datasets must not be committed. The
repository retains code, documentation, checksum records, and aggregate results
under the policy described in the data card. CSV exports are determined by the
SQL you supply; the runner does not enforce aggregation.

## Offline tests

```powershell
python -m pytest
```

The committed tests cover SHA256 calculations and manifest conflicts, successful
and interrupted downloads with mocked network responses, and DuckDB connection
configuration and cleanup. They use temporary files, run offline, and do not
require the real dataset.
