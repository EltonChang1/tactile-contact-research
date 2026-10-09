# Implementation checks — 8 October 2026

`python -m pytest -q`: **24 passed**. `python -m compileall -q src tests scripts` also completed successfully.

The checks exercise physical amplitude scaling and modeled-band RMS; native-time motion fitting under delivery jitter; disjoint specimen splits; support/query condition exclusions; prefix windows; target-independent prediction inputs; training-only normalization and retrieval; linear-power response averaging; invalid bootstrap groups; finite masked inputs and support-order invariance; wrong-support derangement; checkpoint restoration; tiny-fit optimization; fresh pipeline exports/provenance; immutable download hashes; and separate synthetic/measured output roots.

Real-data execution: 120 recording triplets audited; 100 selected windows; 88 matched episodes; three initialization seeds completed with selected checkpoints at epoch 9. Conditions-only, copy, retrieval, model, and wrong-support predictions were saved on the same eight validation episodes. Baseline coefficients/library entries and their source-window IDs are retained alongside raw predictions.

Synthetic execution: the fixture configuration completed across five protocols and three durations. These fixtures establish I/O and algorithm behavior, not real contact dynamics. Test fixtures use temporary roots and do not modify downloaded measurements.

The local runtime used Python 3.12.6, NumPy 1.26.4, SciPy 1.15.1, and PyTorch 2.6.0+cu118 on CPU. The complete environment snapshot is in `results/environment.lock.txt`. Source, data, window/episode, and split hashes are recorded in `results/run_manifest.json`.

The first fresh-run export exposed a missing output-directory initialization; it was corrected and now has an end-to-end regression check. Preparation also exposed overly fragmented steady intervals; that data-audit issue was investigated using training recordings and is documented separately in `development_status.md`.

No locked test evaluation, force identification, forward simulation, or robot-learning experiment was run. The initial encoder does not demonstrate an advantage over retrieval on the provisional development validation set.
