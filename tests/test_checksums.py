"""Test file integrity using small local files, without the real dataset."""

from hashlib import sha256

import pytest

from src import checksums


@pytest.mark.parametrize("content", [b"", b"abc", b"multiple chunks of file content"])
def test_file_sha256_matches_known_digest(tmp_path, monkeypatch, content):
    path = tmp_path / "sample.bin"
    path.write_bytes(content)
    monkeypatch.setattr(checksums, "CHUNK_SIZE", 4)

    assert checksums.file_sha256(path) == sha256(content).hexdigest()


def test_verify_sha256_rejects_modified_file(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"original")
    expected = checksums.file_sha256(path)
    assert checksums.verify_sha256(path, expected) == expected

    path.write_bytes(b"modified")

    with pytest.raises(ValueError, match="SHA256 mismatch"):
        checksums.verify_sha256(path, expected)


def test_record_checksum_preserves_other_entries_and_is_idempotent(tmp_path):
    manifest = tmp_path / "data/CHECKSUMS.txt"
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    for path in [first, second]:
        checksums.record_checksum(path, manifest=manifest, root=tmp_path)

    original_manifest = manifest.read_bytes()
    checksums.record_checksum(first, manifest=manifest, root=tmp_path)

    assert manifest.read_bytes() == original_manifest
    assert checksums.read_checksums(manifest) == {
        "first.bin": sha256(b"first").hexdigest(),
        "second.bin": sha256(b"second").hexdigest(),
    }
    assert not manifest.with_name("CHECKSUMS.txt.tmp").exists()


def test_record_checksum_rejects_conflict_without_rewriting(tmp_path):
    path = tmp_path / "sample.bin"
    manifest = tmp_path / "CHECKSUMS.txt"
    path.write_bytes(b"original")
    checksums.record_checksum(path, manifest=manifest, root=tmp_path)
    original_manifest = manifest.read_bytes()
    path.write_bytes(b"modified")

    with pytest.raises(ValueError, match="Conflicting checksum"):
        checksums.record_checksum(path, manifest=manifest, root=tmp_path)

    assert manifest.read_bytes() == original_manifest


def test_missing_file_does_not_create_manifest(tmp_path):
    manifest = tmp_path / "CHECKSUMS.txt"

    with pytest.raises(FileNotFoundError):
        checksums.record_checksum(
            tmp_path / "missing.bin", manifest=manifest, root=tmp_path
        )

    assert not manifest.exists()


def test_invalid_manifest_is_rejected(tmp_path):
    manifest = tmp_path / "CHECKSUMS.txt"
    manifest.write_text("invalid checksum record\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid checksum record"):
        checksums.read_checksums(manifest)


def test_verification_command_is_read_only(tmp_path, monkeypatch, capsys):
    path = tmp_path / "sample.bin"
    manifest = tmp_path / "CHECKSUMS.txt"
    path.write_bytes(b"verified")
    digest = checksums.record_checksum(path, manifest=manifest, root=tmp_path)
    original_manifest = manifest.read_bytes()
    monkeypatch.setattr(checksums, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checksums, "RAW_PATH", path)
    monkeypatch.setattr(checksums, "CHECKSUMS_PATH", manifest)
    monkeypatch.setattr(checksums, "EXPECTED_RAW_SHA256", digest)

    checksums.main()

    assert digest in capsys.readouterr().out
    assert manifest.read_bytes() == original_manifest

    manifest.unlink()

    with pytest.raises(ValueError, match="No recorded checksum"):
        checksums.main()

    assert not manifest.exists()
