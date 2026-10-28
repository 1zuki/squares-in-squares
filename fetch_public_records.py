"""Fetch public catalogue SVG records with a manifest and SHA-256 hashes."""

from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

CATALOGUE = "https://kingbird.myphotos.cc/packing/squares_in_squares.html"
OUT = Path("data/public_records")
PATTERN = re.compile(r"(?:href|src)=['\"](square-(\d+)[A-Za-z0-9_-]*\.svg)['\"]", re.I)


def fetch(url: str, attempts: int = 5) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; squares-in-squares-research/1.0)",
            "Accept": "text/html, image/svg+xml;q=0.9, */*;q=0.5",
        },
    )
    last_error = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - retry transient public-host failures
            last_error = exc
            if attempt + 1 == attempts:
                break
            time.sleep(min(8.0, 1.0 + 2.0**attempt))
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    svg_dir = OUT / "svg"
    svg_dir.mkdir(exist_ok=True)
    source_html = OUT / "source.html"
    html = source_html.read_bytes() if source_html.exists() else fetch(CATALOGUE)
    source_html.write_bytes(html)
    links = sorted({(name, int(n)) for name, n in PATTERN.findall(html.decode("utf-8", errors="replace"))})
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"catalogue": CATALOGUE, "records": []}
    known = {item["file"]: item for item in manifest["records"]}
    for name, n in links:
        target = svg_dir / name
        url = CATALOGUE.rsplit("/", 1)[0] + "/" + name
        if not target.exists() or target.stat().st_size == 0:
            try:
                target.write_bytes(fetch(url))
            except Exception as exc:  # noqa: BLE001 - checkpoint and continue through transient failures
                print(f"skip {name}: {exc}")
                continue
            time.sleep(0.35)
        known[name] = {"n": n, "file": name, "url": url, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
        manifest["records"] = sorted(known.values(), key=lambda item: (item["n"], item["file"]))
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    missing = len(links) - len(known)
    print(f"catalogue links={len(links)} downloaded={len(known)} missing={missing} into {svg_dir}")


if __name__ == "__main__":
    main()
