from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

import numpy as np
import pandas as pd
import torch
from torch.utils.data import TensorDataset,DataLoader,WeightedRandomSampler

from .config import write_json
from .models import ContactPredictor


def validation_objective(episodes, predictions, targets):
    data = episodes[["surface_id","protocol","duration_s"]].copy()
    data["error"] = np.abs(predictions-targets).mean(axis=1)
    return float(data.groupby(["protocol","duration_s","surface_id"]).error.mean().groupby(level=[0,1]).mean().mean())


def fit_model(root, cfg, train, val, store, scaler, seed):
    if not (train.split == "train").all() or not (val.split == "val").all():
        raise ValueError("Training and checkpoint selection require separate splits")
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    settings = cfg["training"]
    model = ContactPredictor(latent_dim=settings["latent_dim"])
    optimizer = torch.optim.Adam(model.parameters(),lr=settings["learning_rate"])
    arrays = store.batch_inputs(train,scaler)
    target = store.targets(train)
    dataset = TensorDataset(*(torch.from_numpy(a) for a in arrays),torch.from_numpy(target))
    counts = train.groupby(["surface_id","protocol","duration_s"]).episode_id.transform("size")
    generator = torch.Generator().manual_seed(seed)
    samples = settings["episodes_per_surface"]*train.surface_id.nunique()
    sampler = WeightedRandomSampler(torch.as_tensor(1/counts.to_numpy(),dtype=torch.double),samples,replacement=True,generator=generator)
    loader = DataLoader(dataset,batch_size=settings["batch_size"],sampler=sampler)
    val_inputs = tuple(torch.from_numpy(a) for a in store.batch_inputs(val,scaler))
    val_target = store.targets(val)
    best,stale,best_epoch = np.inf,0,0
    history = []
    for epoch in range(1,settings["epochs"]+1):
        model.train(); losses = []
        for support,mask,q,y in loader:
            optimizer.zero_grad(set_to_none=True)
            prediction,_ = model(support,mask,q)
            loss = torch.nn.functional.l1_loss(prediction,y)
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step(); losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            predictions = model(*val_inputs)[0].numpy()
        score = validation_objective(val,predictions,val_target)
        history.append({"epoch":epoch,"train_loss":float(np.mean(losses)),"validation_equal_cell_mae":score})
        if score < best:
            best,best_epoch,stale = score,epoch,0
            state = deepcopy(model.state_dict())
        else:
            stale += 1
        if stale >= settings["patience"]:
            break
    model.load_state_dict(state); model.eval()
    run = Path(root)/"runs"/cfg["config_hash"]/f"seed_{seed}"
    run.mkdir(parents=True,exist_ok=True)
    torch.save({"state_dict":state,"seed":seed,"selected_epoch":best_epoch,
                "config_hash":cfg["config_hash"],"support_dim":101,"output_dim":96,
                "latent_dim":settings["latent_dim"],"scaler_mean":torch.from_numpy(scaler["mean"]),
                "scaler_std":torch.from_numpy(scaler["std"])},run/"model.pt")
    pd.DataFrame(history).to_csv(run/"history.csv",index=False)
    write_json(run/"config.json",cfg)
    print(f"Seed {seed}: selected epoch {best_epoch}, validation MAE {best:.4f}",flush=True)
    return model,run/"model.pt"


def model_predictions(model, episodes, store, scaler):
    model.eval()
    with torch.no_grad():
        return model(*(torch.from_numpy(a) for a in store.batch_inputs(episodes,scaler)))[0].numpy()
