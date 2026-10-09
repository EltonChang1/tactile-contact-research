"""Revision-pinned bounded downloads; original bytes and hashes are preserved."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request
import time

from .config import file_hash, write_json, data_root, recording_permitted


def download_cluster(root, cfg):
    root = data_root(root,cfg)
    revision = cfg["revision"]
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Download requires a pinned 40-character dataset commit")
    raw = root / "data/raw/cluster"
    source_path = root / "data/source.json"
    if source_path.exists():
        import json
        source = json.loads(source_path.read_text())
        if source.get("source_kind") != "cluster" or source.get("revision") != revision or source.get("repo_id") != cfg["repo_id"]:
            raise ValueError("Existing raw directory belongs to another dataset revision")
    files = ["README.md", "texture_list.xlsx"]
    for surface in cfg["train_ids"] + cfg["val_ids"]:
        for speed, direction, force in cfg["conditions"]:
            if not recording_permitted(cfg,surface,speed):
                continue
            for repeat in [0, 1]:
                stem = f"{surface}_{direction}_{speed}_{round(force * 1000)}_{repeat}.parquet"
                files.extend(f"sensor_data/{modality}/{surface}/{stem}" for modality in ["accel", "force", "position"])
    files = sorted(set(files))
    inventory_path = root / "data/raw_inventory.json"
    old = {}
    if inventory_path.exists():
        import json
        old = {r["path"]: r for r in json.loads(inventory_path.read_text())["files"]}

    def fetch(relative):
        path = raw / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and relative in old:
            if file_hash(path) != old[relative]["sha256"]:
                raise ValueError(f"Raw-data hash mismatch: {relative}")
        elif not path.exists():
            url = f"https://huggingface.co/datasets/{cfg['repo_id']}/resolve/{revision}/{relative}"
            temp = path.with_suffix(path.suffix + ".tmp")
            for attempt in range(3):
                try:
                    request = urllib.request.Request(url, headers={"User-Agent": "tactile-contact-research/0.1"})
                    with urllib.request.urlopen(request, timeout=90) as response, temp.open("wb") as output:
                        while chunk := response.read(1024 * 1024):
                            output.write(chunk)
                    temp.replace(path)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(1 + attempt)
        return {"path": relative, "bytes": path.stat().st_size, "sha256": file_hash(path)}

    write_json(source_path, {"repo_id": cfg["repo_id"], "revision": revision,
                             "source_kind": "cluster", "selected_surface_ids": cfg["train_ids"] + cfg["val_ids"]})
    inventory = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch,relative) for relative in files]
        try:
            for future in as_completed(futures):
                record = future.result()
                inventory.append(record); old[record["path"]] = record
                if len(inventory) % 50 == 0:
                    write_json(inventory_path, {"revision":revision,"files":[old[k] for k in sorted(old)]})
                    print(f"Verified {len(inventory)}/{len(files)} raw files",flush=True)
        finally:
            # A failed/interrupted selection retains hashes of completed downloads.
            write_json(inventory_path, {"revision":revision,"files":[old[k] for k in sorted(old)]})
    print(f"Downloaded/verified {len(inventory)} files ({sum(r['bytes'] for r in inventory)/1e6:.1f} MB)", flush=True)
