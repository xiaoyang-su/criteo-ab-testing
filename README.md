# Criteo Advertising Incrementality: An A/B Testing Portfolio

This data science portfolio develops a reproducible, retrospective analysis of
Criteo's corrected Uplift v2.1 benchmark, reported to contain 13,979,592 user-level
records from randomized advertising incrementality tests. The central question
is whether advertising eligibility increased website visits relative to holdout
assignment, with conversions as a secondary business outcome.

The planned analysis uses `treatment` for assignment-based comparisons. Actual
advertising `exposure` occurs after assignment. The released data were subsampled
and anonymized, so future estimates will be interpreted within the benchmark
setting rather than as the original campaigns' incrementality or measured ROI.

**Status:** Data download, SHA256 verification, Gzip CSV-to-Parquet conversion,
DuckDB connections, and SQL-file execution are implemented. The local raw archive
and generated Parquet both have entries in `data/CHECKSUMS.txt`. Schema auditing,
experiment metrics, and statistical analysis remain pending; the two files in
`sql/` are currently empty placeholders.

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

Write and save your SQL in `sql/` before executing it. The current placeholder
files need content; the runner rejects an empty file. Each run verifies the
Parquet and registers it as the session view **`criteo`**, which your SQL can query.
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

The standalone DuckDB CLI is another optional way to explore data interactively.
It runs independently of these Python scripts and does not automatically apply
the project's checksum verification, connection settings, or `criteo` view.

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
|   |-- 00_schema_audit.sql          # Empty placeholder
|   `-- 02_experiment_metrics.sql    # Empty placeholder
|-- tests/
|   |-- test_checksums.py
|   |-- test_download.py
|   `-- test_db.py
|-- data/
|   |-- CHECKSUMS.txt                # Tracked integrity records
|   |-- raw/                        # Downloaded archive; ignored by Git
|   |-- processed/                  # Generated Parquet; ignored by Git
|   `-- tmp/                        # DuckDB spill directory; generated as needed
|-- results/                        # Query outputs; only aggregates belong in Git
|-- notebooks/                      # Reserved for subsequent analysis
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
