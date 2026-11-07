"""Shared paths and verified data access for the local Criteo pipeline."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from duckdb import DuckDBPyConnection

from src.checksums import (
    CHECKSUMS_PATH,
    EXPECTED_RAW_SHA256,
    PROJECT_ROOT,
    RAW_PATH,
    read_checksums,
    verify_sha256,
)


ROOT = PROJECT_ROOT
RAW = RAW_PATH
PARQUET = ROOT / "data/processed/criteo_v2_1.parquet"
TEMP_DIRECTORY = ROOT / "data/tmp"


def project_path(path: str | Path) -> Path:
    """Resolve a relative path from the project root, not the caller's directory."""
    return (ROOT / Path(path)).resolve()


def verify_checksum(path: str | Path) -> str:
    """Verify a project data file against its existing checksum record."""
    path = project_path(path)
    relative_path = path.relative_to(ROOT).as_posix()
    expected = read_checksums(CHECKSUMS_PATH).get(relative_path)

    if expected is None:
        raise ValueError(f"No recorded checksum: {relative_path}")

    return verify_sha256(path, expected)


def verify_raw_archive() -> str:
    """Require the raw archive to match both the manifest and official SHA256."""
    digest = verify_checksum(RAW)

    if digest != EXPECTED_RAW_SHA256:
        raise ValueError("The raw archive does not match the official SHA256")

    return digest


def configure_temp_storage(connection: DuckDBPyConnection) -> None:
    """Keep DuckDB spill files under the project's ignored data directory."""
    TEMP_DIRECTORY.mkdir(parents=True, exist_ok=True)
    connection.execute("SET temp_directory = ?", [str(TEMP_DIRECTORY)])


def register_parquet(connection: DuckDBPyConnection) -> None:
    """Expose the verified Parquet as the criteo view without loading a DataFrame."""
    verify_checksum(PARQUET)
    connection.read_parquet(str(PARQUET)).create_view("criteo")


@contextmanager
def project_directory() -> Iterator[None]:
    """Resolve user-written SQL file paths from the root, then restore the cwd."""
    previous_directory = Path.cwd()

    try:
        os.chdir(ROOT)
        yield
    finally:
        os.chdir(previous_directory)
