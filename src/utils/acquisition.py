"""Resumable source acquisition with immutable raw files and safe ZIP handling."""

import logging
import shutil
import stat
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import requests

from utils.data_loader import read_json, sha256, write_json


def safe_extract(archive: Path, destination: Path, max_bytes: int) -> list[Path]:
    """Preflight all ZIP members; reject traversal, symlinks, and oversized archives."""
    root = destination.resolve()
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if sum(info.file_size for info in members) > max_bytes:
            raise ValueError("Archive exceeds configured extraction limit")
        for info in members:
            name = PurePosixPath(info.filename.replace("\\", "/"))
            mode = info.external_attr >> 16
            target = (root / str(name)).resolve()
            if (
                name.is_absolute()
                or ".." in name.parts
                or ":" in str(name)
                or not target.is_relative_to(root)
                or stat.S_ISLNK(mode)
            ):
                raise ValueError(f"Unsafe archive member: {info.filename}")
        outputs = []
        for info in members:
            path = root / info.filename
            if info.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                # Check existing bytes against archive content rather than replacing raw data.
                with zipped.open(info) as source:
                    import hashlib

                    existing = hashlib.sha256(source.read()).hexdigest()
                if sha256(path) != existing:
                    raise ValueError(f"Existing raw file differs from source archive: {path}")
            else:
                with zipped.open(info) as source, path.open("xb") as output:
                    shutil.copyfileobj(source, output)
            outputs.append(path)
    return outputs


def acquire(ctx) -> list[Path]:
    """Download once with bounded retries and preserve source hashes and UTC retrieval time."""
    source = ctx.config["source"]
    raw = ctx.path("data", "raw")
    raw.mkdir(parents=True, exist_ok=True)
    archive, metadata = raw / source["archive"], raw / "provenance.json"
    if archive.exists() and metadata.exists():
        prior = read_json(metadata)
        if sha256(archive) != prior["archive_sha256"]:
            raise ValueError(
                "Raw archive checksum changed; restore original or use a new data directory"
            )
        if source["url"] != prior["url"]:
            raise ValueError("Configured source changed; use a new data directory")
    elif archive.exists():
        raise ValueError("Existing archive has no provenance; move it aside before acquisition")
    else:
        partial = raw / (source["archive"] + ".part")
        for attempt in range(source["retries"]):
            try:
                with requests.get(
                    source["url"], stream=True, timeout=(20, source["timeout_seconds"])
                ) as response:
                    response.raise_for_status()
                    size, announced = 0, int(response.headers.get("Content-Length", 0))
                    with partial.open("wb") as stream:
                        for chunk in response.iter_content(1024 * 1024):
                            stream.write(chunk)
                            size += len(chunk)
                            if size // (5 * 1024 * 1024) != (size - len(chunk)) // (
                                5 * 1024 * 1024
                            ):
                                logging.info("download_bytes=%s expected_bytes=%s", size, announced)
                    if size == 0 or (announced and size != announced):
                        raise ValueError("Incomplete HTTP response")
                    if not zipfile.is_zipfile(partial):
                        raise ValueError("Source response is not a ZIP archive")
                    actual = sha256(partial)
                    if source["expected_sha256"] and actual != source["expected_sha256"]:
                        raise ValueError("Download SHA-256 does not match configured expected hash")
                    partial.replace(archive)
                    write_json(
                        {
                            **source,
                            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                            "archive_sha256": actual,
                            "bytes": size,
                            "http_etag": response.headers.get("ETag"),
                            "checksum_scope": "Locally recorded integrity; no publisher checksum advertised.",
                        },
                        metadata,
                    )
                break
            except (requests.RequestException, ValueError) as exc:
                logging.warning("download_attempt=%s error=%s", attempt + 1, exc)
                partial.unlink(missing_ok=True)
                if attempt + 1 == source["retries"]:
                    raise RuntimeError(f"Could not acquire public source: {source['url']}") from exc
                time.sleep(2**attempt)
    if source["expected_sha256"] and sha256(archive) != source["expected_sha256"]:
        raise ValueError("Existing archive fails configured checksum")
    extracted = safe_extract(archive, raw, source["max_extracted_bytes"])
    if not (raw / source["workbook"]).exists():
        raise FileNotFoundError(f"Expected workbook absent: {source['workbook']}")
    return [archive, metadata] + extracted
