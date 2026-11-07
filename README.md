**Criteo Advertising Incrementality: An A/B Testing Portfolio**
This project develops a reproducible, retrospective analysis of Criteo’s corrected Uplift v2.1 benchmark, containing approximately 14 million user-level records from randomized advertising incrementality tests. It examines assignment-based differences in website visits and conversions, evaluates statistical precision, and explores how the findings inform decisions under explicit cost and value assumptions.

**Status:** Data download, integrity checks, and test infrastructure are implemented. Data conversion and analysis are pending.
Website visits are the primary outcome, with conversions reported as a secondary business outcome. The released data were subsampled and anonymized, so estimates are interpreted within the benchmark setting and are not presented as the original campaigns’ incrementality or measured ROI.

## Local setup

Use the existing Conda environment, `abtest`, from the project root. The commands
below explicitly select that environment; activating `.venv` is unnecessary.
The infrastructure requires Python 3.10 or later, DuckDB, and pytest. The broader
project dependencies are listed in `requirements.txt`.

```powershell
conda run -n abtest python -m pytest
conda run --no-capture-output -n abtest python -m src.download_data
conda run -n abtest python -m src.checksums
```

The download command streams the compressed archive from the
[official Criteo mirror](https://huggingface.co/datasets/criteo/criteo-uplift/blob/main/criteo-research-uplift-v2.1.csv.gz)
to `data/raw/criteo-research-uplift-v2.1.csv.gz`. It checks the published SHA256
before accepting the file and recording it in `data/CHECKSUMS.txt`. File locations
are resolved from the project root, independently of the working directory.

The expected SHA256 of the compressed archive is:

```text
2716e1bf0fd157a93b5bf86924d9088419dfbac2022c6cd90030220634f616dc
```

An existing valid archive is verified and reused. A corrupt archive or conflicting
checksum record causes an error rather than an overwrite. Network errors are
retried up to three times, restarting from the beginning. Failed transfers clean
up their `.part` file. The standalone checksum command verifies both the official
hash and the recorded checksum without changing either file.

Raw and processed datasets are ignored by Git. The checksum manifest may be
committed. Tests use temporary files and mocked network responses, so they run
offline without downloading the real dataset.

## DuckDB connection template

```python
from src.db import connect_database

with connect_database() as connection:
    # Add your own queries here.
    pass
```

The default is an independent in-memory connection with a `4GB` DuckDB memory
limit and one thread. Override these with `memory_limit` and `threads`, or pass a
database file path as the first argument. Relative database paths are resolved
from the project root; their parent directories must already exist. Keep any
dataset-bearing database under `data/` so it remains ignored by Git. DuckDB's
memory limit does not cap the entire Python process.

The connection helper does not load data, create views, or run analysis files.
CSV conversion, schema audits, statistical analysis, and synthetic data generation
remain pending.
