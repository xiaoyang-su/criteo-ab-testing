"""Create explicit DuckDB connections without loading or transforming data."""

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def connect_database(
    database: str | Path = ":memory:",
    *,
    memory_limit: str = "4GB",
    threads: int = 1,
) -> duckdb.DuckDBPyConnection:
    """Return a configured connection; the caller is responsible for closing it.

    Relative database paths resolve from the project root. Parent directories
    for persistent databases must already exist.
    """
    if str(database) != ":memory:":
        database_path = Path(database)

        if not database_path.is_absolute():
            database_path = PROJECT_ROOT / database_path

        database = str(database_path.resolve())

    connection = duckdb.connect(database=str(database))

    try:
        connection.execute("SET memory_limit = ?", [memory_limit])
        connection.execute("SET threads = ?", [threads])
    except Exception:
        connection.close()
        raise

    return connection
