"""SHA256 helpers and a read-only verification command for the raw archive."""

from hashlib import sha256
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data/raw/criteo-research-uplift-v2.1.csv.gz"
CHECKSUMS_PATH = PROJECT_ROOT / "data/CHECKSUMS.txt"
EXPECTED_RAW_SHA256 = (
    "2716e1bf0fd157a93b5bf86924d9088419"
    "dfbac2022c6cd90030220634f616dc"
)
CHUNK_SIZE = 8 * 1024 * 1024


def file_sha256(path: Path) -> str:
    """Hash a file in bounded chunks, without loading it into memory."""
    digest = sha256()

    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)

    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> str:
    """Return the actual digest, raising ValueError on a mismatch."""
    actual = file_sha256(path)

    if actual != expected:
        raise ValueError(
            f"SHA256 mismatch for {path}: expected {expected}, got {actual}"
        )

    return actual


def read_checksums(manifest: Path = CHECKSUMS_PATH) -> dict[str, str]:
    """Read a SHA256 manifest keyed by project-relative POSIX paths."""
    manifest = Path(manifest)

    if not manifest.exists():
        return {}

    entries = {}

    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue

        parts = line.split(maxsplit=1)

        if (
            len(parts) != 2
            or len(parts[0]) != 64
            or any(character not in "0123456789abcdef" for character in parts[0])
        ):
            raise ValueError(f"Invalid checksum record in {manifest}: {line!r}")

        digest, relative_path = parts

        if relative_path in entries and entries[relative_path] != digest:
            raise ValueError(f"Conflicting checksum records: {relative_path}")

        entries[relative_path] = digest

    return entries


def record_checksum(
    path: Path,
    *,
    manifest: Path = CHECKSUMS_PATH,
    root: Path = PROJECT_ROOT,
) -> str:
    """Add a checksum atomically, preserving existing integrity baselines."""
    path = Path(path).resolve()
    manifest = Path(manifest)
    relative_path = path.relative_to(Path(root).resolve()).as_posix()
    digest = file_sha256(path)
    entries = read_checksums(manifest)
    previous = entries.get(relative_path)

    if previous is not None:
        if previous != digest:
            raise ValueError(f"Conflicting checksum record: {relative_path}")
        return digest

    entries[relative_path] = digest
    content = "".join(
        f"{value}  {name}\n" for name, value in sorted(entries.items())
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest.with_name(manifest.name + ".tmp")

    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(manifest)
    finally:
        temporary.unlink(missing_ok=True)

    return digest


def main() -> None:
    """Check both the official hash and the existing manifest; never rewrite it."""
    digest = verify_sha256(RAW_PATH, EXPECTED_RAW_SHA256)
    relative_path = RAW_PATH.relative_to(PROJECT_ROOT).as_posix()
    recorded = read_checksums(CHECKSUMS_PATH).get(relative_path)

    if recorded is None:
        raise ValueError(f"No recorded checksum: {relative_path}")

    if recorded != digest:
        raise ValueError(f"Conflicting checksum record: {relative_path}")

    print(f"Verified against the official SHA256 and manifest: {relative_path}")
    print(f"SHA256: {digest}")


if __name__ == "__main__":
    main()
