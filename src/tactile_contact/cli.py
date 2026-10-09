from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config


def main(argv=None):
    parser = argparse.ArgumentParser(description="Brief-contact development pipeline (locked test evaluation disabled)")
    parser.add_argument("command",choices=["download","audit","prepare","run","synth","figures","timing"])
    parser.add_argument("--config",default="configs/pilot.yaml")
    parser.add_argument("--root",default=".",help="Data/results directory; configuration path is relative to the current shell")
    parser.add_argument("--reuse",action="store_true",help="Reuse manifests whose configuration hash matches exactly")
    parser.add_argument("--data-root",help="Shared raw-data root; derived data/results remain under --root")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    if args.data_root:
        if cfg["source_kind"] != "cluster":
            parser.error("--data-root is supported for measured Cluster data only")
        # Operational path is excluded from the scientific configuration hash.
        cfg["data_root"] = str(Path(args.data_root).resolve())
    root = Path(args.root).resolve(); root.mkdir(parents=True,exist_ok=True)
    if args.command == "download":
        if cfg["source_kind"] != "cluster":
            parser.error("download requires Cluster configuration")
        from .download import download_cluster
        download_cluster(root,cfg)
    elif args.command == "synth":
        from .synthetic import generate
        generate(root,cfg)
    elif args.command == "audit":
        from .audit import build_manifest
        build_manifest(root,cfg)
    elif args.command == "prepare":
        from .pipeline import prepare
        prepare(root,cfg)
    elif args.command == "run":
        from .pipeline import run
        run(root,cfg,args.reuse)
    elif args.command == "timing":
        from .timing import timing_sensitivity
        timing_sensitivity(root,cfg)
    else:
        import pandas as pd
        from .evaluation import make_figures
        make_figures(root,cfg,pd.read_csv(root/"results/tables/summary.csv"))


if __name__ == "__main__":
    main()
