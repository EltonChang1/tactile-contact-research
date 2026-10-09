"""Compare a predeclared training specimen with original CSV archive members.

Download at most 32 MiB, never the full 15 GB archive; raw CSVs stay ignored.
Run from the repository root after downloading configs/omitted_speed.yaml.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd

from tactile_contact.config import file_hash, load_config, write_json, validate_source
from tactile_contact.source_archive import RangeReader, read_member


ARTICLE = "https://api.figshare.com/v2/articles/29438288/versions/6"
# Chosen before inspecting original CSVs; known speeds, both loads, three directions.
RECORDS = ["0_0_20_500_0", "0_0_40_500_0", "0_0_40_1000_1",
           "0_90_40_500_0", "0_45_60_1000_1"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("runs/clock_qc_review"))
    args = parser.parse_args()
    cfg = load_config("configs/omitted_speed.yaml")
    validate_source(Path("."), cfg)
    convention_path = Path("configs/clock_convention.json")
    convention = json.loads(convention_path.read_text())
    if any(cfg[key] != convention[key] for key in ["time_base", "sampling_rate_hz"]) or convention["physical_acquisition_clock_verified"]:
        raise ValueError("Source review expects the declared uncalibrated logged-coordinate convention")
    inventory = {row["path"]: row["sha256"] for row in json.loads(Path("data/raw_inventory.json").read_text())["files"]}
    if 0 not in cfg["train_ids"]:
        raise ValueError("Source review is restricted to declared training specimen 0")
    cache = args.root/"source"
    cache.mkdir(parents=True, exist_ok=True)
    metadata_path = cache/"figshare_v6.json"
    if not metadata_path.exists():
        with urllib.request.urlopen(ARTICLE, timeout=30) as response:
            metadata_path.write_bytes(response.read(1024**2))
    metadata = json.loads(metadata_path.read_text())
    source = next(f for f in metadata["files"] if f["id"] == 61118716)
    reader = RangeReader(source["download_url"], source["size"])
    rows = []
    with zipfile.ZipFile(reader) as archive:
        infos = archive.infolist()
        for record in RECORDS:
            for channel, columns in [("accel", ["X", "Y", "Z"]), ("force", ["force"]), ("position", ["X", "Y"])]:
                suffix = f"sensor_data/{channel}/0/{record}.csv"
                matches = [info for info in infos if info.filename.endswith(suffix)]
                if len(matches) != 1:
                    raise ValueError(f"Expected unique original CSV: {suffix}")
                info = matches[0]
                local = cache/channel/f"{record}.csv"
                local.parent.mkdir(exist_ok=True)
                # Always re-fetch bounded members, so CRC/member identity is rechecked.
                body = read_member(archive, info)
                local.write_bytes(body)
                original = pd.read_csv(io.BytesIO(body), float_precision="round_trip")
                parquet = Path(f"data/raw/cluster/sensor_data/{channel}/0/{record}.parquet")
                if file_hash(parquet) != inventory[parquet.relative_to("data/raw/cluster").as_posix()]:
                    raise ValueError("Mirror file differs from immutable download inventory")
                mirror = pd.read_parquet(parquet)
                if len(original) != len(mirror):
                    raise ValueError(f"Original/mirror row mismatch for {suffix}")
                ns = np.rint(original.time.to_numpy()*1e9).astype(np.int64)
                delta = np.abs(ns-mirror.time_ns.to_numpy())
                signals = original[columns].to_numpy().astype(np.float32)
                signal_equal = np.array_equal(signals, mirror[columns].to_numpy())
                if delta.max() > 1 or not signal_equal:
                    raise ValueError(f"Unexpected conversion difference for {suffix}")
                t = original.time.to_numpy()
                rows.append(dict(recording_id=record, channel=channel, archive_member=info.filename,
                    rows=len(t), original_mean_logged_rate_hz=(len(t)-1)/(t[-1]-t[0]),
                    max_rounded_timestamp_difference_ns=int(delta.max()), float32_signal_exact=bool(signal_equal),
                    original_sha256=hashlib.sha256(body).hexdigest(), mirror_sha256=file_hash(parquet),
                    member_crc32=f"{info.CRC:08x}", member_bytes=info.file_size, compressed_bytes=info.compress_size))
                print(record, channel, len(t), int(delta.max()), signal_equal, flush=True)
    target = Path("docs/clock_source_comparison.csv")
    pd.DataFrame(rows).to_csv(target, index=False, lineterminator="\n")
    provenance = dict(article_api=ARTICLE, article_version=metadata["version"],
        archive={k: source[k] for k in ["id", "name", "size", "download_url", "supplied_md5", "computed_md5"]},
        archive_md5_verified=False, member_crc_verified=True, ranges=reader.ranges,
        transferred_bytes=reader.transferred, byte_budget=reader.budget,
        selected_records=RECORDS, selection_scope="training specimen 0; known speeds only; selected before reading originals",
        config_hash=cfg["config_hash"], mirror_revision=cfg["revision"],
        convention_id=convention["convention_id"], convention_sha256=file_hash(convention_path),
        script_sha256=file_hash(__file__), reader_sha256=file_hash("src/tactile_contact/source_archive.py"),
        table_sha256=file_hash(target),
        conclusion="Bounded conversion check only. Preserved timestamps do not establish sensor acquisition timing.")
    write_json("docs/clock_source_provenance.json", provenance)
    print("Bounded archive bytes:", reader.transferred, flush=True)


if __name__ == "__main__":
    main()
