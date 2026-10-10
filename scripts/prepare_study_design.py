"""Review metadata and reserve groups without loading new sensor responses.

--audit-local captures historical manifests/cache names (no sensor values).
--check-config checks development access against the committed reservation;
it is an explicit preflight, not a locked test-scoring implementation.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import urllib.request

import pandas as pd
import yaml

from tactile_contact.config import file_hash, write_json
from tactile_contact.records import parse_record_name
from tactile_contact.study_design import (reviewed_groups, reserve_groups, validate_reservation,
                                          validate_development_access, query_domains)


RULES = Path("configs/specimen_review_rules.json")
EXPOSURE = Path("configs/development_exposure.json")
GROUPS = Path("configs/all_specimen_groups.csv")
RESERVATION = Path("configs/test_reservation.csv")


def metadata_file(rules):
    path = Path("data/raw/cluster/texture_list.xlsx")
    if not path.exists():
        path = Path("runs/study_design/source/texture_list.xlsx")
        if not path.exists():
            url = f"https://huggingface.co/datasets/{rules['repo_id']}/resolve/{rules['revision']}/texture_list.xlsx"
            with urllib.request.urlopen(url, timeout=30) as response:
                body = response.read(1024**2+1)
            if len(body) > 1024**2:
                raise ValueError("Metadata download exceeds 1 MiB")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
    if file_hash(path) != rules["metadata_sha256"]:
        raise ValueError("Metadata differs from pinned original hash")
    return path


def capture_local_exposure(exposure, revision):
    approved = set(exposure["training_surface_ids"]+exposure["selection_surface_ids"])
    evidence, events, accessed = {}, [], defaultdict(set)
    for root_name in exposure["historical_real_run_roots"]:
        root = Path(root_name)
        manifest = root/"results/run_manifest.json"
        recording_path = root/"data/manifests/recordings.csv"
        windows_path = root/"data/manifests/windows.csv"
        episodes_path = root/"data/manifests/episodes.csv"
        for path in [manifest, recording_path, windows_path, episodes_path]:
            evidence[path.as_posix()] = file_hash(path)
        run = json.loads(manifest.read_text())
        cfg = run["config"]
        if run["stage"] != "development" or cfg["source_kind"] != "cluster" or cfg["revision"] != revision:
            raise ValueError("Historical exposure source mismatch")
        recordings, windows, episodes = [pd.read_csv(path) for path in [recording_path, windows_path, episodes_path]]
        if not set(recordings.surface_id).issubset(approved):
            raise ValueError("Unexpected additional historical signal exposure; update the explicit exposure snapshot")
        for row in recordings.itertuples():
            accessed[row.recording_id].add(root_name)
        for surface in sorted(set(recordings.surface_id)):
            role = "training" if surface in cfg["train_ids"] else "selection_and_exploratory_scoring"
            ep = episodes[episodes.surface_id == surface]
            events.append(dict(run_root=root_name, surface_id=surface, role=role,
                recording_triplets=int((recordings.surface_id == surface).sum()),
                prepared_windows=int((windows.surface_id == surface).sum()), query_episodes=len(ep),
                query_speeds_mm_s="|".join(map(str, sorted(ep.query_speed_mm_s.unique()))),
                config_hash=cfg["config_hash"], run_manifest_sha256=evidence[manifest.as_posix()],
                recording_manifest_sha256=evidence[recording_path.as_posix()],
                windows_manifest_sha256=evidence[windows_path.as_posix()], episodes_sha256=evidence[episodes_path.as_posix()]))
    inventory_path = Path("data/raw_inventory.json")
    inventory = json.loads(inventory_path.read_text())
    if inventory["revision"] != revision:
        raise ValueError("Cache inventory revision mismatch")
    cache = defaultdict(set)
    for entry in inventory["files"]:
        path = Path(entry["path"])
        if path.parts[:2] == ("sensor_data", "accel"):
            record = parse_record_name(path)
            if record["surface_id"] not in approved:
                raise ValueError("Cache has undeclared specimen exposure; do not promote it to fresh test")
        if len(path.parts) == 4 and path.parts[0] == "sensor_data" and path.suffix == ".parquet":
            cache[path.stem].add(path.parts[1])
    if not set(accessed).issubset(set(cache)) or any(modalities != {"accel", "force", "position"} for modalities in cache.values()):
        raise ValueError("Historical recording union is missing complete cached triplets")
    records = []
    for record in sorted(accessed):
        row = parse_record_name(record+".parquet")
        records.append(dict(row, cached_channels=3, observed_in_run_roots="|".join(sorted(accessed[record]))))
    pd.DataFrame(events).to_csv("docs/development_exposure_events.csv", index=False, lineterminator="\n")
    pd.DataFrame(records).to_csv("docs/development_record_access.csv", index=False, lineterminator="\n")
    write_json("docs/local_exposure_snapshot.json", dict(source_revision=revision,
        manifest_hashes=evidence, inventory_sha256=file_hash(inventory_path), cached_recording_triplets=len(cache),
        historical_recording_triplets=len(accessed),
        scope="Historical configuration/manifests/cache filenames audited. No additional sensor values read. Twelve specimens permanently development-exposed."))


def check_config(path):
    cfg = yaml.safe_load(path.read_text())
    if cfg["stage"] != "development" or cfg["source_kind"] != "cluster":
        raise ValueError("This preflight is for measured development selections; locked scoring is not implemented")
    exposure = json.loads(EXPOSURE.read_text())
    exposed = exposure["training_surface_ids"]+exposure["selection_surface_ids"]
    validate_development_access(cfg["train_ids"]+cfg["val_ids"], pd.read_csv(GROUPS), pd.read_csv(RESERVATION), exposed)
    print("Development reservation preflight passed:", path, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-local", action="store_true")
    parser.add_argument("--check-config", type=Path)
    args = parser.parse_args()
    if args.check_config:
        check_config(args.check_config)
        return
    rules, exposure = [json.loads(path.read_text()) for path in [RULES, EXPOSURE]]
    exposed = exposure["training_surface_ids"]+exposure["selection_surface_ids"]
    metadata_path = metadata_file(rules)
    fields = ["Texture_id", "Texture_Name (en)", "Category", "Sub Category"]
    metadata = pd.read_excel(metadata_path, usecols=fields).rename(columns=dict(zip(fields, ["surface_id", "name", "category", "subcategory"])))
    metadata = metadata.fillna("")
    for column in ["name", "category", "subcategory"]:
        metadata[column] = metadata[column].astype(str).str.replace("\\n", " ", regex=False).str.strip()
    expected = set(range(rules["expected_surface_ids"]["first"], rules["expected_surface_ids"]["last"]+1))
    if metadata.surface_id.duplicated().any() or set(metadata.surface_id) != expected:
        raise ValueError("Metadata IDs differ from the complete expected list")
    groups = reviewed_groups(metadata, rules)
    reservation = reserve_groups(groups, exposed, rules["reservation"]["category_specimen_targets"], rules["reservation"]["seed"])
    validate_reservation(groups, reservation, exposed)
    if RESERVATION.exists():
        prior = pd.read_csv(RESERVATION)
        validate_reservation(groups, prior, exposed)
        if set(prior.surface_id) != set(reservation.surface_id):
            raise ValueError("Existing reservation would change; require an explicit versioned review instead of silent reselection")
    if args.audit_local:
        capture_local_exposure(exposure, rules["revision"])
    records = pd.read_csv("docs/development_record_access.csv")
    if set(records.surface_id) != set(exposed):
        raise ValueError("Committed access snapshot disagrees with declared exposure")
    group_exposed = set(groups.loc[groups.surface_id.isin(exposed), "family_group"])
    reserved = set(reservation.surface_id)
    ledger = groups[["surface_id", "name", "category", "family_group"]].copy()
    ledger["metadata_reviewed"] = True
    ledger["signal_development_exposed"] = ledger.surface_id.isin(exposed)
    ledger["group_development_exposed"] = ledger.family_group.isin(group_exposed)
    ledger["historical_recordings_before_wider_qc"] = ledger.surface_id.map(records.groupby("surface_id").size()).fillna(0).astype(int)
    ledger["role_at_snapshot"] = ["development_training" if i in exposure["training_surface_ids"] else "development_selection_and_scores" if i in exposure["selection_surface_ids"] else "related_to_development_group" if g in group_exposed else "reserved_future_test" if i in reserved else "metadata_only_unassigned" for i, g in zip(ledger.surface_id, ledger.family_group)]
    ledger["fresh_test_group_candidate"] = ~ledger.group_development_exposed
    ledger["reserved_future_test"] = ledger.surface_id.isin(reserved)
    groups.to_csv(GROUPS, index=False, lineterminator="\n")
    reservation = reservation[["surface_id", "name", "category", "family_group"]].copy()
    reservation["reservation_id"] = rules["reservation"]["id"]
    reservation["reservation_status"] = "metadata_only_reserved_protocol_pending"
    reservation.to_csv(RESERVATION, index=False, lineterminator="\n")
    ledger.to_csv("docs/specimen_exposure_ledger.csv", index=False, lineterminator="\n")
    domains = query_domains()
    domains.to_csv("configs/query_domains.csv", index=False, lineterminator="\n")
    columns = ["support_condition", "familiar_query", "known_speed_query", "omitted_candidate", "omitted_transfer", "matched_familiar_fit_query"]
    counts = {column: int(domains[column].sum()) for column in columns}
    categories = groups.groupby("category").agg(specimens=("surface_id", "size"), groups=("family_group", "nunique")).reset_index()
    for name, mask in [("signal_exposed", ledger.signal_development_exposed), ("group_blocked", ledger.group_development_exposed), ("reserved", ledger.reserved_future_test)]:
        categories[name] = categories.category.map(ledger[mask].groupby("category").size()).fillna(0).astype(int)
    categories.to_csv("docs/specimen_category_review.csv", index=False, lineterminator="\n")
    design = dict(design_id="wider_development_domains_v1", status="Domain/access planning; models and locked scoring not implemented here",
        clock_convention="logged_coordinates_v1", query_domain_counts=counts,
        familiar_primary=dict(fit_query_domain="familiar_query", score_query_domain="familiar_query", before_qc=76),
        matched_omitted_comparison=dict(shared_selection_query_domain="known_speed_query", shared_score_query_domain="omitted_transfer",
            familiar_fit_query_domain="matched_familiar_fit_query", omitted_fit_query_domain="known_speed_query",
            familiar_fit_queries=70, omitted_fit_queries=44, score_queries=26,
            rule="Identical specimens, support/query windows, QC intersection, methods, tuning and known-speed selection; only add the 26 transfer-speed training response triples in familiar fit. Both transfer score pools stay unread until selections finish."),
        known_speed_qc_review=dict(surface_ids=exposure["training_surface_ids"], speeds_mm_s=[20, 40, 60], directions_deg=list(range(0, 360, 45)),
            nominal_loads_N=[.5, 1.], repeats=[0, 1], requested_recording_triplets=960,
            rule="Known-speed training-only coverage first; mandatory reservation preflight in the wider runner. No reserved signals or model fits; downloads restricted to ten already exposed training specimens."),
        reservation_preflight="python scripts/prepare_study_design.py --check-config CONFIG_PATH",
        access_limit="Explicit preflight only; the existing pipeline does not automatically invoke it. Locked test access/scoring still requires implementation before scientific evaluation.")
    write_json("configs/study_design.json", design)
    outputs = [GROUPS, RESERVATION, Path("configs/query_domains.csv"), Path("configs/study_design.json"),
        Path("docs/specimen_exposure_ledger.csv"), Path("docs/specimen_category_review.csv"),
        Path("docs/development_exposure_events.csv"), Path("docs/development_record_access.csv"), Path("docs/local_exposure_snapshot.json")]
    # Export JSON with LF so Git normalization preserves its recorded byte hash.
    for path in [Path("configs/study_design.json"), Path("docs/local_exposure_snapshot.json")]:
        path.write_text(path.read_text(), encoding="utf-8", newline="\n")
    write_json("docs/study_design_provenance.json", dict(review_id=rules["review_id"], source_revision=rules["revision"],
        metadata_sha256=file_hash(metadata_path), input_hashes={path.as_posix(): file_hash(path) for path in [RULES, EXPOSURE]},
        source_hashes={"scripts/prepare_study_design.py": file_hash(__file__), **{f"src/tactile_contact/{name}.py": file_hash(f"src/tactile_contact/{name}.py") for name in ["study_design", "config", "records"]}},
        evidence_hashes={path: file_hash(path) for path in exposure["evidence"]},
        output_hashes={path.as_posix(): file_hash(path) for path in outputs},
        specimens=len(groups), reviewed_groups=int(groups.family_group.nunique()), direct_exposed_specimens=len(exposed),
        group_blocked_specimens=int(ledger.group_development_exposed.sum()), fresh_group_candidate_specimens=int(ledger.fresh_test_group_candidate.sum()),
        reserved_specimens=len(reservation), reserved_groups=int(reservation.family_group.nunique()),
        reserved_surface_ids=sorted(reserved), domain_counts=counts,
        limitations="Metadata-name/analyst uncertainty blocks only; no verified manufacture independence. Reservation precedes wider sensor/QC review and does not constitute a frozen scientific test. Historical manifests are locally auditable; their committed snapshot can be used on a clean clone."))
    print(categories.to_string(index=False), flush=True)
    print("Groups:", groups.family_group.nunique(), "Group-blocked:", ledger.group_development_exposed.sum(), "Reserved:", sorted(reserved), flush=True)
    print(counts, flush=True)


if __name__ == "__main__":
    main()
