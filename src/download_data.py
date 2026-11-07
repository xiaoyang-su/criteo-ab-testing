"""Download the official Criteo archive and verify it before accepting it."""

from http.client import IncompleteRead
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.checksums import (
    CHECKSUMS_PATH,
    EXPECTED_RAW_SHA256,
    PROJECT_ROOT,
    RAW_PATH,
    read_checksums,
    record_checksum,
    verify_sha256,
)


URL = (
    "https://huggingface.co/datasets/criteo/criteo-uplift/"
    "resolve/main/criteo-research-uplift-v2.1.csv.gz"
)


CHUNK_SIZE = 8 * 1024 * 1024
MAX_ATTEMPTS = 3


def download_data(
    destination: Path = RAW_PATH,
    *,
    manifest: Path = CHECKSUMS_PATH,
    project_root: Path = PROJECT_ROOT,
) -> Path:
    """Download once, or verify and reuse an existing official archive."""
    destination = Path(destination).resolve()
    manifest = Path(manifest).resolve()
    relative_path = destination.relative_to(project_root.resolve()).as_posix()
    recorded = read_checksums(manifest).get(relative_path)

    if recorded is not None and recorded != EXPECTED_RAW_SHA256:
        raise ValueError(f"Conflicting checksum record: {relative_path}")

    if destination.exists():
        verify_sha256(destination, EXPECTED_RAW_SHA256)
        record_checksum(destination, manifest=manifest, root=project_root)
        print(f"Existing archive verified; download skipped: {destination}")
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    request = Request(
        URL,
        headers={"User-Agent": "criteo-ab-test-portfolio/1.0"},
    )

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"Downloading (attempt {attempt}/{MAX_ATTEMPTS}): {URL}", flush=True)

            try:
                with urlopen(request, timeout=30) as response:
                    with temporary.open("wb") as output:
                        downloaded = 0
                        next_report = 64 * 1024 * 1024

                        while chunk := response.read(CHUNK_SIZE):
                            output.write(chunk)
                            downloaded += len(chunk)

                            if downloaded >= next_report:
                                print(f"Downloaded {downloaded / 1024**2:.0f} MiB", flush=True)
                                next_report += 64 * 1024 * 1024

                break
            except (URLError, TimeoutError, ConnectionError, IncompleteRead):
                temporary.unlink(missing_ok=True)

                if attempt == MAX_ATTEMPTS:
                    raise

                print("Network error; restarting the download.", flush=True)

        digest = verify_sha256(temporary, EXPECTED_RAW_SHA256)
        temporary.replace(destination)

        try:
            record_checksum(destination, manifest=manifest, root=project_root)
        except Exception:
            # Do not leave a new archive accepted without its integrity record.
            destination.unlink(missing_ok=True)
            raise

        print(f"Saved: {destination}")
        print(f"SHA256: {digest}")
        return destination
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    download_data()


if __name__ == "__main__":
    main()
