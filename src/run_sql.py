"""Run a supplied SQL file against the verified Parquet via the criteo view.

Usage: python -m src.run_sql sql/your_query.sql [--output results/your_result.csv]
Run without a SQL filename to choose from a numbered list under sql/.
Direct execution is also supported: python src/run_sql.py
All statements execute; only the final statement's result is displayed or saved.
"""

import argparse
import csv
import sys
from pathlib import Path
from uuid import uuid4

# VS Code's Run Python File action executes this file outside package mode.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duckdb import DuckDBPyConnection

from src import data
from src.db import connect_database


def save_result(connection: DuckDBPyConnection, output: Path) -> None:
    """Stream the final result to CSV, without replacing an existing output."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.stem}.{uuid4().hex}.tmp.csv")

    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(column[0] for column in connection.description)

            while rows := connection.fetchmany(10_000):
                writer.writerows(rows)

        if output.exists():
            raise FileExistsError(f"Refusing to replace existing output: {output}")

        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def run_sql(
    sql_file: str | Path,
    *,
    output: str | Path | None = None,
    preview_rows: int = 20,
) -> Path | None:
    """Execute user SQL; preview the last result or export it in bounded batches."""
    if preview_rows <= 0:
        raise ValueError("preview_rows must be positive")

    sql_path = data.project_path(sql_file)
    sql = sql_path.read_text(encoding="utf-8-sig")

    if not sql.strip():
        raise ValueError(f"SQL file is empty: {sql_path}")

    output_path = data.project_path(output) if output is not None else None

    if output_path is not None:
        if output_path.suffix.lower() != ".csv":
            raise ValueError("The output path must end with .csv")
        if output_path == sql_path:
            raise ValueError("The output path must not replace the SQL file")
        if output_path.exists():
            raise FileExistsError(f"Refusing to replace existing output: {output_path}")

    with data.project_directory():
        with connect_database() as connection:
            data.configure_temp_storage(connection)
            data.register_parquet(connection)
            connection.execute(sql)

            if connection.description is None:
                if output_path is not None:
                    raise ValueError("The final SQL statement produced no result to save")
                print("The SQL file produced no result set.")
            elif output_path is not None:
                save_result(connection, output_path)
                print(f"Saved: {output_path}")
            else:
                writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
                writer.writerow(column[0] for column in connection.description)
                rows = connection.fetchmany(preview_rows + 1)
                writer.writerows(rows[:preview_rows])

                if len(rows) > preview_rows:
                    print(
                        f"Showing the first {preview_rows} rows. "
                        "Use --output to save the complete final result."
                    )

    print(f"Completed: {sql_path.name}")
    return output_path


def select_sql_file() -> Path | None:
    """Prompt for a SQL file; return None when the user cancels."""
    sql_directory = data.ROOT / "sql"
    sql_files = sorted(
        (path for path in sql_directory.rglob("*.sql") if path.is_file()),
        key=lambda path: path.relative_to(sql_directory).as_posix().casefold(),
    )

    if not sql_files:
        raise SystemExit(f"No SQL files found in: {sql_directory}")

    print("Available SQL files:")

    for number, path in enumerate(sql_files, start=1):
        print(f"  {number}. {path.relative_to(data.ROOT).as_posix()}")

    while True:
        try:
            selection = input("Enter a file number, or q to cancel: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSelection cancelled.")
            return None

        if selection.lower() in {"q", "quit", "exit"}:
            print("Selection cancelled.")
            return None

        try:
            number = int(selection)
        except ValueError:
            number = 0

        if 1 <= number <= len(sql_files):
            selected = sql_files[number - 1]
            print(f"Selected: {selected.relative_to(data.ROOT).as_posix()}")
            return selected

        print(f"Please enter a number from 1 to {len(sql_files)}, or q to cancel.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sql_file",
        nargs="?",
        help="SQL file path relative to the project root; omit to choose interactively",
    )
    parser.add_argument("--output", help="Optional CSV path for the final result")
    parser.add_argument(
        "--preview-rows", type=int, default=20, help="Maximum displayed rows (default: 20)"
    )
    arguments = parser.parse_args()
    sql_file = arguments.sql_file if arguments.sql_file is not None else select_sql_file()

    if sql_file is None:
        return

    run_sql(
        sql_file,
        output=arguments.output,
        preview_rows=arguments.preview_rows,
    )


if __name__ == "__main__":
    main()
