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
from .config import write_json,file_hash


def prepare(root,cfg):
    manifest = build_manifest(root,cfg)
    windows = extract_windows(root,cfg,manifest)
    episodes = build_episodes(root,cfg,windows)
    print(f"Prepared {len(windows)} windows and {len(episodes)} episodes",flush=True)
    return windows,episodes


def run(root,cfg,reuse=False):
    # Importing torch and regression is delayed so data auditing does not require training initialization.
    from .baselines import ConditionsOnly,CopySpectrum,Retrieval
    from .training import fit_model,model_predictions
    from .evaluation import score_predictions,summarize,wrong_support
    root = Path(root)
    if reuse:
        windows = pd.read_csv(root/"data/manifests/windows.csv")
        episodes = pd.read_csv(root/"data/manifests/episodes.csv")
        if set(windows.window_config_hash) != {cfg["config_hash"]} or set(episodes.config_hash) != {cfg["config_hash"]}:
            raise ValueError("Prepared features/episodes belong to another configuration; rerun prepare")
    else:
        windows,episodes = prepare(root,cfg)
    train = episodes[episodes.split == "train"].reset_index(drop=True)
    val = episodes[episodes.split == "val"].reset_index(drop=True)
    if set(train.surface_id) & set(val.surface_id):
        raise ValueError("Surface split leakage")
    store = FeatureStore(root,windows)
    scaler = store.fit_scaler(train)
    target = store.targets(val)
    (root/"results/tables").mkdir(parents=True,exist_ok=True)
    scores = []
    predictions = {}
    for name,baseline in [("conditions_only",ConditionsOnly().fit(train,store,scaler)),("copy",CopySpectrum()),
                           ("retrieval",Retrieval().fit(train,store,scaler))]:
        output = baseline.predict(val,store,scaler)
        prediction,retrieved = output if isinstance(output,tuple) else (output,None)
        predictions[name] = prediction
        scores.append(score_predictions(val,prediction,target,name,-1,cfg["power_floor"],retrieved))
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
    checkpoints = []
    for seed in cfg["training"]["seeds"]:
        model,path = fit_model(root,cfg,train,val,store,scaler,seed)
        checkpoints.append(path.relative_to(root).as_posix())
        prediction = model_predictions(model,val,store,scaler)
        predictions[f"encoder_{seed}"] = prediction
        scores.append(score_predictions(val,prediction,target,"encoder",seed,cfg["power_floor"]))
        if val.surface_id.nunique() > 1:
            substituted = wrong_support(val)
            substituted.to_csv(root/"results/tables/wrong_support_assignments.csv",index=False)
            wrong = model_predictions(model,substituted,store,scaler)
            predictions[f"encoder_wrong_support_{seed}"] = wrong
            scores.append(score_predictions(val,wrong,target,"encoder_wrong_support",seed,cfg["power_floor"]))
    result = pd.concat(scores,ignore_index=True)
    table = summarize(root,cfg,result)
    # Preserve actual predicted/target arrays, not just errors.
    np.savez_compressed(root/"results/tables/predictions.npz",episode_ids=val.episode_id.to_numpy(dtype=str),
                        targets=target,**predictions)
    manifests = {name:file_hash(root/"data/manifests"/name) for name in ["recordings.csv","surfaces.csv","split_materials.csv","windows.csv","episodes.csv","eligibility.csv"]}
    source = json.loads((root/"data/source.json").read_text())
    software_hashes = {p.name:file_hash(p) for p in Path(__file__).parent.glob("*.py")}
    write_json(root/"results/run_manifest.json",{"stage":"development","source":source,"config":cfg,
        "manifest_hashes":manifests,"software_hashes":software_hashes,"checkpoints":checkpoints,"python":platform.python_version(),
        "platform":platform.platform(),"device":"cpu",
        "claim_limit":"Provisional time base and unreviewed Cluster family groups; validation only, no scientific test."})
    freeze = subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True)
    (root/"results/environment.lock.txt").write_text(freeze.stdout,encoding="utf-8")
    print(table.to_string(index=False),flush=True)
    print(f"Saved validation tables, predictions, figures, and checkpoints under {root.resolve()}",flush=True)
    return table
