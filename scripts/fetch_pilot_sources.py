"""Fetch only three curated public CC BY advisories; no keys, teachers, or broad crawl."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data/pilot/v1/sources"
PATHS = {
    "GHSA-f82v-jwr5-mffw": "advisories/github-reviewed/2025/03/GHSA-f82v-jwr5-mffw/GHSA-f82v-jwr5-mffw.json",
    "GHSA-cpwx-vrp4-4pq7": "advisories/github-reviewed/2025/03/GHSA-cpwx-vrp4-4pq7/GHSA-cpwx-vrp4-4pq7.json",
    "GHSA-9hjg-9r4m-mvj7": "advisories/github-reviewed/2025/06/GHSA-9hjg-9r4m-mvj7/GHSA-9hjg-9r4m-mvj7.json",
}


def fetch(url):
    request = Request(url, headers={"User-Agent": "valar-llm-pilot-source-snapshot"})
    with urlopen(request, timeout=30) as response:
        data = response.read(1_000_001)
    if len(data) > 1_000_000:
        raise ValueError("Public source exceeds snapshot byte budget")
    return data


def main():
    if TARGET.exists() and any(TARGET.iterdir()):
        raise SystemExit("Source snapshot already exists; preserve this revision")
    commit = json.loads(fetch("https://api.github.com/repos/github/advisory-database/commits/main"))["sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Expected an immutable GitHub commit")
    base = f"https://raw.githubusercontent.com/github/advisory-database/{commit}/"
    license_data = fetch(base + "LICENSE.md")
    if b"Attribution 4.0 International" not in license_data:
        raise ValueError("License snapshot requires manual review")
    snapshots = []
    collected = []
    for identifier, source_path in PATHS.items():
        raw = fetch(base + source_path)
        document = json.loads(raw)
        if document["id"] != identifier:
            raise ValueError("Unexpected advisory identity")
        collected.append((identifier + ".json", raw))
        snapshots.append({"id": identifier, "file": "sources/" + identifier + ".json",
                          "revision": commit, "sha256": hashlib.sha256(raw).hexdigest(),
                          "url": base + source_path, "upstream_path": source_path,
                          "attribution": "GitHub Advisory Database contributors",
                          "license": "CC-BY-4.0", "license_url": base + "LICENSE.md"})
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "LICENSE.github-advisory-database.md").write_bytes(license_data)
    for filename, raw in collected:
        (TARGET / filename).write_bytes(raw)
    lock = {"schema_version": "1", "repository": "https://github.com/github/advisory-database",
            "revision": commit, "fetched_at": datetime.now(timezone.utc).isoformat(),
            "license_file": "sources/LICENSE.github-advisory-database.md",
            "license_sha256": hashlib.sha256(license_data).hexdigest(), "sources": snapshots}
    (TARGET.parent / "sources.lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(snapshots)} licensed sources at immutable revision {commit}")


if __name__ == "__main__":
    main()
