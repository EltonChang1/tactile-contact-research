from __future__ import annotations

from pathlib import Path
import json
import platform
import subprocess
import sys

import numpy as np
import pandas as pd

from .audit import build_manifest
from .windows import extract_windows
from .episodes import build_episodes,FeatureStore
from .config import write_json,file_hash,validate_source,omitted_speed,validate_fit_pool


def preparation_hashes():
    return {name:file_hash(Path(__file__).with_name(name)) for name in
            ["audit.py","windows.py","episodes.py","signal.py","records.py","config.py"]}


def prepare(root,cfg):
    manifest = build_manifest(root,cfg)
    windows = extract_windows(root,cfg,manifest)
    episodes = build_episodes(root,cfg,windows)
    write_json(Path(root)/"data/manifests/preparation.json",{
        "config_hash":cfg["config_hash"],"software_hashes":preparation_hashes()})
    print(f"Prepared {len(windows)} windows and {len(episodes)} episodes",flush=True)
    return windows,episodes


def run(root,cfg,reuse=False):
    # Importing torch and regression is delayed so data auditing does not require training initialization.
    from .baselines import ConditionsOnly,CopySpectrum,Retrieval,FixedFeatures,SpeedRescaling
    from .training import fit_model,model_predictions
    from .evaluation import score_predictions,summarize,wrong_support
    root = Path(root)
    source = validate_source(root,cfg)
    if reuse:
        provenance_path = root/"data/manifests/preparation.json"
        if not provenance_path.exists() or json.loads(provenance_path.read_text())["software_hashes"] != preparation_hashes():
            raise ValueError("Preparation code changed or provenance is missing; rerun prepare")
        windows = pd.read_csv(root/"data/manifests/windows.csv")
        episodes = pd.read_csv(root/"data/manifests/episodes.csv")
        if set(windows.window_config_hash) != {cfg["config_hash"]} or set(episodes.config_hash) != {cfg["config_hash"]}:
            raise ValueError("Prepared features/episodes belong to another configuration; rerun prepare")
    else:
        windows,episodes = prepare(root,cfg)
    train = episodes[episodes.split == "train"].reset_index(drop=True)
    val = episodes[episodes.split == "val"].reset_index(drop=True)
    selection = val[val.evaluation_partition == "selection"].reset_index(drop=True)
    validate_fit_pool(train,"train"); validate_fit_pool(selection,"val")
    if set(train.surface_id) & set(val.surface_id):
        raise ValueError("Surface split leakage")
    store = FeatureStore(root,windows)
    scaler = store.fit_scaler(train)
    (root/"results/tables").mkdir(parents=True,exist_ok=True)
    outputs = []
    predictions = {}
    write_json(root/"results/tables/fit_selection_manifest.json",{
        "experiment":cfg.get("experiment","familiar_conditions"),"config_hash":cfg["config_hash"],
        "fit_query_window_ids":sorted(train.query_window_id.unique().tolist()),
        "fit_speeds_mm_s":sorted(train.query_speed_mm_s.unique().tolist()),
        "selection_query_window_ids":sorted(selection.query_window_id.unique().tolist()),
        "selection_speeds_mm_s":sorted(selection.query_speed_mm_s.unique().tolist()),
        "transfer_query_window_ids":sorted(val[val.evaluation_partition == "transfer"].query_window_id.unique().tolist()),
        "target_access_rule":"Transfer targets are read for scoring only after every baseline and checkpoint is selected."})
    for name,baseline in [("conditions_only",ConditionsOnly().fit(train,store,scaler)),("copy",CopySpectrum()),
                           ("retrieval",Retrieval(interpolate_speeds=omitted_speed(cfg)).fit(train,store,scaler)),
                           ("fixed_features",FixedFeatures().fit(train,selection,store,scaler)),
                           ("speed_rescaling",SpeedRescaling().fit(train,selection,store,scaler))]:
        output = baseline.predict(val,store,scaler)
        prediction,retrieved = output if isinstance(output,tuple) else (output,None)
        predictions[name] = prediction
        outputs.append((name,-1,prediction,retrieved))
        if name == "conditions_only":
            np.savez_compressed(root/"results/tables/conditions_only_fit.npz",coefficient=baseline.regression.coef_,
                                intercept=baseline.regression.intercept_,alpha=np.array(1.))
        elif name == "retrieval":
            arrays = {}
            sources = {"library":{},"responses":{}}
            for (protocol,duration),(fingerprints,ids) in baseline.library.items():
                key = f"{protocol}_{duration:g}"
                arrays[f"fingerprints_{key}"] = fingerprints
                arrays[f"training_ids_{key}"] = ids
                sources["library"][key] = baseline.library_sources[(protocol,duration)]
            for key,response in baseline.responses.items():
                label = "_".join(str(v) for v in key)
                arrays[f"response_{label}"] = response
                sources["responses"][label] = baseline.response_sources[key]
            np.savez_compressed(root/"results/tables/retrieval_fit.npz",**arrays)
            write_json(root/"results/tables/retrieval_sources.json",sources)
            write_json(root/"results/tables/retrieval_prediction_sources.json",{
                "rule":"linear interpolation of log band power" if omitted_speed(cfg) else "recorded training responses",
                "predictions":baseline.prediction_sources})
        elif name == "fixed_features":
            np.savez_compressed(root/"results/tables/fixed_features_fit.npz",coefficient=baseline.regression.coef_,
                intercept=baseline.regression.intercept_,feature_mean=baseline.mean,feature_std=baseline.std,alpha=baseline.alpha)
            write_json(root/"results/tables/fixed_features_selection.json",{
                "selected_alpha":baseline.alpha,"candidates":baseline.candidates,"fit_surface_ids":baseline.fit_surface_ids,
                "selection_surface_ids":sorted(selection.surface_id.unique().tolist()),"features":"mean/std of support vectors, count, query conditions"})
        elif name == "speed_rescaling":
            write_json(root/"results/tables/speed_rescaling_fit.json",{
                "selected_alpha":baseline.alpha,"p":float(baseline.exponents[0]),"b":float(baseline.exponents[1]),
                "candidates":baseline.candidates,"fit_surface_ids":baseline.fit_surface_ids,
                "fit_support_window_ids":baseline.fit_support_window_ids,"fit_query_window_ids":baseline.fit_query_window_ids,
                "selection_surface_ids":sorted(selection.surface_id.unique().tolist()),
                "direction_rule":"nearest circular angle, then absolute log speed ratio, then canonical order",
                "fit_rule":"weighted above-floor log-power ridge; p bounded [-4,8], b [-4,4]; validation selects alpha"})
    checkpoints = []
    for seed in cfg["training"]["seeds"]:
        model,path = fit_model(root,cfg,train,selection,store,scaler,seed)
        checkpoints.append(path.relative_to(root).as_posix())
        prediction = model_predictions(model,val,store,scaler)
        predictions[f"encoder_{seed}"] = prediction
        outputs.append(("encoder",seed,prediction,None))
        if val.surface_id.nunique() > 1:
            substituted = wrong_support(val)
            substituted.to_csv(root/"results/tables/wrong_support_assignments.csv",index=False)
            wrong = model_predictions(model,substituted,store,scaler)
            predictions[f"encoder_wrong_support_{seed}"] = wrong
            outputs.append(("encoder_wrong_support",seed,wrong,None))
    # Transfer targets stay unread until weights, hyperparameters and checkpoints are fixed.
    target = store.targets(val)
    scores = [score_predictions(val,prediction,target,name,seed,cfg["power_floor"],retrieved)
              for name,seed,prediction,retrieved in outputs]
    result = pd.concat(scores,ignore_index=True)
    table = summarize(root,cfg,result)
    # Preserve actual predicted/target arrays, not just errors.
    np.savez_compressed(root/"results/tables/predictions.npz",episode_ids=val.episode_id.to_numpy(dtype=str),
                        evaluation_partitions=val.evaluation_partition.to_numpy(dtype=str),targets=target,**predictions)
    manifests = {name:file_hash(root/"data/manifests"/name) for name in ["recordings.csv","surfaces.csv","split_materials.csv","windows.csv","episodes.csv","eligibility.csv"]}
    software_hashes = {p.name:file_hash(p) for p in Path(__file__).parent.glob("*.py")}
    write_json(root/"results/run_manifest.json",{"stage":"development","source":source,"config":cfg,
        "manifest_hashes":manifests,"software_hashes":software_hashes,"checkpoints":checkpoints,"python":platform.python_version(),
        "platform":platform.platform(),"device":"cpu",
        "claim_limit":"Provisional time base; specimen grouping scope limited to available metadata; development validation only."})
    freeze = subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True)
    (root/"results/environment.lock.txt").write_text(freeze.stdout,encoding="utf-8")
    primary_protocol = "single" if "single" in cfg["protocols"] else cfg["protocols"][0]
    primary_duration = .5 if .5 in cfg["durations_s"] else cfg["durations_s"][0]
    print(f"Validation: {primary_protocol}, {primary_duration:g} s support (full matrix saved to summary.csv)",flush=True)
    primary = table[(table.protocol == primary_protocol) & (table.duration_s == primary_duration)]
    if omitted_speed(cfg):
        primary = primary[primary.evaluation_partition == "transfer"]
    print(primary.to_string(index=False),flush=True)
    print(f"Saved validation tables, predictions, figures, and checkpoints under {root.resolve()}",flush=True)
    return table
