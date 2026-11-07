"""Convert the verified Gzip CSV to Parquet: python -m src.prepare_data."""

import argparse
from pathlib import Path
from uuid import uuid4

from src import data
from src.checksums import read_checksums, record_checksum
from src.db import connect_database


def prepare_data() -> Path:
    """Create one ZSTD Parquet copy, preserving the source columns and values."""
    if data.PARQUET.exists():
        digest = data.verify_checksum(data.PARQUET)
        print(f"Existing Parquet verified; conversion skipped: {data.PARQUET}")
        print(f"SHA256: {digest}")
        return data.PARQUET

    relative_path = data.PARQUET.relative_to(data.ROOT).as_posix()

    if relative_path in read_checksums(data.CHECKSUMS_PATH):
        raise FileNotFoundError(
            f"The recorded Parquet is missing: {data.PARQUET}. "
            "Restore the verified file rather than replacing its checksum baseline."
        )

    data.verify_raw_archive()
    data.PARQUET.parent.mkdir(parents=True, exist_ok=True)
    temporary = data.PARQUET.with_name(
        f".{data.PARQUET.stem}.{uuid4().hex}.tmp.parquet"
    )

    print(f"Converting: {data.RAW}", flush=True)

    try:
        with connect_database() as connection:
            data.configure_temp_storage(connection)
            connection.execute("SET preserve_insertion_order = true")
            source = connection.read_csv(
                str(data.RAW),
                header=True,
                compression="gzip",
                parallel=False,
            )
            source.write_parquet(str(temporary), compression="zstd")

        temporary.replace(data.PARQUET)

        try:
            digest = record_checksum(
                data.PARQUET,
                manifest=data.CHECKSUMS_PATH,
                root=data.ROOT,
            )
        except Exception:
            # A new output is accepted only when its integrity record is saved.
            data.PARQUET.unlink(missing_ok=True)
            raise
    finally:
        temporary.unlink(missing_ok=True)

    print(f"Saved: {data.PARQUET}")
    print(f"SHA256: {digest}")
    return data.PARQUET


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    prepare_data()


if __name__ == "__main__":
    main()
