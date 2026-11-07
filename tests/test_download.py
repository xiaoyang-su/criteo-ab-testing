"""Exercise the download lifecycle with mocked network responses only."""

from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace
from urllib.error import URLError
from unittest.mock import Mock

import pytest

from src import download_data as downloader
from src.checksums import read_checksums, record_checksum


@pytest.fixture
def download_case(tmp_path, monkeypatch):
    payload = b"small offline archive fixture\n"
    destination = tmp_path / "data/raw/archive.csv.gz"
    manifest = tmp_path / "data/CHECKSUMS.txt"
    digest = sha256(payload).hexdigest()
    network = Mock(side_effect=AssertionError("Unexpected network access"))
    monkeypatch.setattr(downloader, "EXPECTED_RAW_SHA256", digest)
    monkeypatch.setattr(downloader, "urlopen", network)

    return SimpleNamespace(
        payload=payload,
        digest=digest,
        destination=destination,
        manifest=manifest,
        part=destination.with_name(destination.name + ".part"),
        root=tmp_path,
        network=network,
        options={
            "destination": destination,
            "manifest": manifest,
            "project_root": tmp_path,
        },
    )


def test_successful_download_records_checksum(download_case):
    case = download_case
    case.network.side_effect = None
    case.network.return_value = BytesIO(case.payload)

    assert downloader.download_data(**case.options) == case.destination
    assert case.destination.read_bytes() == case.payload
    assert read_checksums(case.manifest) == {"data/raw/archive.csv.gz": case.digest}
    assert not case.part.exists()


def test_existing_valid_archive_skips_network(download_case):
    case = download_case
    case.destination.parent.mkdir(parents=True)
    case.destination.write_bytes(case.payload)

    downloader.download_data(**case.options)

    case.network.assert_not_called()
    assert read_checksums(case.manifest)["data/raw/archive.csv.gz"] == case.digest


def test_existing_corrupt_archive_is_not_overwritten(download_case):
    case = download_case
    case.destination.parent.mkdir(parents=True)
    case.destination.write_bytes(b"corrupt")

    with pytest.raises(ValueError, match="SHA256 mismatch"):
        downloader.download_data(**case.options)

    assert case.destination.read_bytes() == b"corrupt"
    assert not case.manifest.exists()
    case.network.assert_not_called()


def test_wrong_download_hash_leaves_no_accepted_files(download_case):
    case = download_case
    case.network.side_effect = None
    case.network.return_value = BytesIO(b"wrong response body")

    with pytest.raises(ValueError, match="SHA256 mismatch"):
        downloader.download_data(**case.options)

    assert not case.destination.exists()
    assert not case.part.exists()
    assert not case.manifest.exists()
    assert case.network.call_count == 1


def test_network_failure_retries_three_times_and_cleans_up(download_case):
    case = download_case
    case.part.parent.mkdir(parents=True)
    case.part.write_bytes(b"stale partial download")
    case.network.side_effect = URLError("offline")

    with pytest.raises(URLError):
        downloader.download_data(**case.options)

    assert case.network.call_count == 3
    assert not case.destination.exists()
    assert not case.part.exists()
    assert not case.manifest.exists()


def test_interrupted_response_restarts_from_the_beginning(download_case):
    case = download_case

    class InterruptedResponse(BytesIO):
        def read(self, size=-1):
            if self.tell() == 0:
                return super().read(5)
            raise ConnectionResetError("connection lost during transfer")

    case.network.side_effect = [
        InterruptedResponse(case.payload),
        BytesIO(case.payload),
    ]

    downloader.download_data(**case.options)

    assert case.network.call_count == 2
    assert case.destination.read_bytes() == case.payload
    assert not case.part.exists()


def test_conflicting_record_fails_before_downloading(download_case):
    case = download_case
    case.manifest.parent.mkdir(parents=True)
    original = f"{'0' * 64}  data/raw/archive.csv.gz\n".encode()
    case.manifest.write_bytes(original)

    with pytest.raises(ValueError, match="Conflicting checksum record"):
        downloader.download_data(**case.options)

    case.network.assert_not_called()
    assert case.manifest.read_bytes() == original
    assert not case.destination.exists()


def test_failed_download_preserves_unrelated_manifest_entries(download_case):
    case = download_case
    other = case.root / "other.bin"
    other.write_bytes(b"other data")
    record_checksum(other, manifest=case.manifest, root=case.root)
    original = case.manifest.read_bytes()
    case.network.side_effect = None
    case.network.return_value = BytesIO(b"wrong response")

    with pytest.raises(ValueError, match="SHA256 mismatch"):
        downloader.download_data(**case.options)

    assert case.manifest.read_bytes() == original
    assert not case.destination.exists()


def test_manifest_write_failure_removes_new_archive(download_case, monkeypatch):
    case = download_case
    case.network.side_effect = None
    case.network.return_value = BytesIO(case.payload)
    monkeypatch.setattr(
        downloader,
        "record_checksum",
        Mock(side_effect=OSError("manifest is not writable")),
    )

    with pytest.raises(OSError, match="not writable"):
        downloader.download_data(**case.options)

    assert not case.destination.exists()
    assert not case.part.exists()
    assert not case.manifest.exists()
