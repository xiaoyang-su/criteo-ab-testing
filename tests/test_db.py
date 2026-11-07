"""Test connection infrastructure using constant queries only."""

import duckdb
import pytest

from src import db


def test_default_connections_are_independent_and_close():
    first = db.connect_database()
    second = db.connect_database()

    try:
        assert first is not second
        assert first.execute("SELECT 42").fetchone() == (42,)
        first.close()
        assert second.execute("SELECT 42").fetchone() == (42,)

        with pytest.raises(duckdb.ConnectionException):
            first.execute("SELECT 42")
    finally:
        first.close()
        second.close()


def test_resource_settings_are_applied():
    with db.connect_database(memory_limit="256MiB", threads=2) as connection:
        assert connection.execute(
            "SELECT current_setting('memory_limit'), current_setting('threads')"
        ).fetchone() == ("256.0 MiB", 2)

    with pytest.raises(duckdb.ConnectionException):
        connection.execute("SELECT 42")


def test_relative_database_path_uses_project_root(tmp_path, monkeypatch):
    working_directory = tmp_path / "elsewhere"
    working_directory.mkdir()
    monkeypatch.setattr(db, "PROJECT_ROOT", tmp_path)
    monkeypatch.chdir(working_directory)

    with db.connect_database("sample.duckdb") as connection:
        assert connection.execute("SELECT 42").fetchone() == (42,)

    assert (tmp_path / "sample.duckdb").exists()
    assert not (working_directory / "sample.duckdb").exists()


def test_configuration_failure_closes_connection(monkeypatch):
    connection = duckdb.connect()
    monkeypatch.setattr(db.duckdb, "connect", lambda **kwargs: connection)

    with pytest.raises(duckdb.Error):
        db.connect_database(memory_limit="invalid")

    with pytest.raises(duckdb.ConnectionException):
        connection.execute("SELECT 42")
