# Implementation checks — 8 October 2026

`python -m pytest -q`: **44 passed**. The ten omitted-speed checks also passed independently. `python -m compileall -q src tests scripts` completed successfully.

The checks exercise physical amplitude scaling and modeled-band RMS; native-time motion fitting under delivery jitter; disjoint specimen splits; support/query condition exclusions; prefix windows; target-independent prediction inputs; training-only normalization and retrieval; linear-power response averaging; invalid bootstrap groups; finite masked inputs and support-order invariance; wrong-support derangement; checkpoint restoration; tiny-fit optimization; fresh pipeline exports/provenance; immutable download hashes; and separate synthetic/measured output roots.

Real-data execution: 120 recording triplets audited; 100 selected windows; 88 matched episodes; three initialization seeds completed with selected checkpoints at epoch 9. Conditions-only, copy, retrieval, model, and wrong-support predictions were saved on the same eight validation episodes. Baseline coefficients/library entries and their source-window IDs are retained alongside raw predictions.

Expanded real execution: all 192 recording triplets passed QC; 268 windows/1,320 episodes across five protocols and three durations; all ten training and two validation specimens remained eligible. Five baselines and three encoder seeds were scored on the same 120 validation episodes. Matched budget contrasts, named subsets, baseline-selection records, and 230 training-window timing comparisons were exported. The initial results remain in their original output directory.

Additional checks cover warp identity, frequency stretching and physical power scaling; extrapolation rejection; train-only fixed-feature statistics; hidden-query independence for both new baselines; canonical support selection; changed clock coordinates/budgets; metadata family conflicts; shared raw-source revision checks; prepared-code invalidation; matching query identities; and invariant ridge regularization when response labels repeat across protocol cells. A float32 regression accumulation discrepancy was corrected by fitting conditions-only ridge in float64.

Omitted-speed checks verify training omitted records are neither downloaded nor opened from a shared cache; fitting/selection partitions contain only permitted speeds; every fitted baseline/scaler rejects transfer labels; a forged fitting partition still rejects omitted query speeds; retrieval interpolates log power rather than using a direct omitted response; missing endpoints/extrapolation fail; configs reject forbidden support endpoints; and transfer targets stay unread until every seed's checkpoint is selected. A fresh synthetic omitted-speed pipeline exports separate selection/transfer summaries, contrasts, and partitioned prediction arrays. The real run completed all three seeds and its report verified 120 transfer interpolations against actual endpoint provenance.

Synthetic execution: the fixture configuration completed across five protocols and three durations. These fixtures establish I/O and algorithm behavior, not real contact dynamics. Test fixtures use temporary roots and do not modify downloaded measurements.

The local runtime used Python 3.12.6, NumPy 1.26.4, SciPy 1.15.1, and PyTorch 2.6.0+cu118 on CPU. The complete environment snapshot is in `results/environment.lock.txt`. Source, data, window/episode, and split hashes are recorded in `results/run_manifest.json`.

The first fresh-run export exposed a missing output-directory initialization; it was corrected and now has an end-to-end regression check. Preparation also exposed overly fragmented steady intervals; that data-audit issue was investigated using training recordings and is documented separately in `development_status.md`.

No locked test evaluation, force identification, forward simulation, or robot-learning experiment was run. The initial encoder does not demonstrate an advantage over retrieval on the provisional development validation set.
