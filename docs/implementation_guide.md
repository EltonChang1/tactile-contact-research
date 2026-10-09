# Tactile Research Implementation Guide

## Brief contact probes for predicting texture and sliding contact

Prepared for Elton Chang — original plan dated 7 October 2026; guide refined 8 October 2026, America/Los_Angeles.

**Purpose:** an implementation guide for the research described in `Tactile_Contact_Research_Plan_2026-10-07.md`. Use the stage gates below to decide which steps are ready to begin. The first completed study uses public data; later milestones add measured contact forces, simulation, and control.

The public study develops the **tactile observation model**: what a robot should sense under a requested contact. The mechanical study develops the **contact law**: forces that influence motion. A useful world model ultimately needs both. Starting with public data lets you test whether brief observations contain transferable information and establish reliable evaluation methods before investing in a force rig. Vibration prediction alone does not identify an intrinsic material law.

**Status as of 8 October 2026:** the specification now has a working bounded development implementation in [tactile-contact-research](https://github.com/EltonChang1/tactile-contact-research). The expanded pilot runs all five support protocols, three durations, five baselines, three encoder seeds, wrong-support controls, matched-budget contrasts, and named diagnostics. See [expanded pilot results](https://github.com/EltonChang1/tactile-contact-research/blob/main/docs/expanded_pilot_report.md) and [implementation checks](https://github.com/EltonChang1/tactile-contact-research/blob/main/docs/implementation_checks.md). Current commands use the package CLI documented in the [README](https://github.com/EltonChang1/tactile-contact-research/blob/main/README.md); individual script names below remain the intended file contracts. Timing, manufacturing-family independence, the full condition grid, and a locked scientific test remain unfinished. The public-data stage has not yet met its scientific completion gate.

The separately fitted [omitted-speed development experiment](https://github.com/EltonChang1/tactile-contact-research/blob/main/docs/omitted_speed_report.md) is also implemented. Fitting and checkpoint selection use only 20/40/60 mm/s; 30/50 mm/s targets remain excluded until scoring. Retrieval interpolates permitted endpoint log spectra, with exact source IDs and weights audited. This bounded experiment still uses provisional development specimens and timing, rather than a locked scientific test.

The numerical defaults are starting choices. Finalize them after a training-data audit, record the decision, and then freeze the evaluation protocol. A result can be scientifically useful even when a simple baseline wins.

## Scope and stage gates

The plan is feasible as a staged project. Its first deliverable is a completed public-data study of brief-contact information. The strongest candidate contribution is the matched-budget experiment and its interpretation; the small network implements that experiment. Hardware-dependent stages need separate access, calibration, and evidence.

| Plan stage | Guide steps | Evidence required before the next stage |
| --- | --- | --- |
| A: tactile-response prediction | 1–17, with packaging in 26 | Locked held-out evaluation, strong baselines, probe-budget results, and a report |
| B: measured sliding mechanics | 18–22 | Independent calibrated force measurements and held-out force predictions |
| C: forward dynamics and engine integration | 23–24 | A dynamically responsive experiment and motion predictions from initial state/actions |
| D: planning or robot learning | 25 | Matched task evaluation after the relevant model has been validated |

Investigate rig access while Stage A runs. Stage A has its own completion point even if hardware remains unavailable. Do Step 26 throughout the project. Static friction, compliance, waveform generation, new sensors, category exclusion, and large policy training are follow-ups whose scope must be justified separately.

## How to use this guide

1. Complete Steps 1–7 to define the question and audit trustworthy data.
2. Build the first complete pipeline through Steps 8–14: `single`, 0.5-second support, the fixed query duration, conditions-only/copy/retrieval baselines, and the small model. Use pilot training surfaces and validation surfaces; leave test targets closed.
3. Verify that this slice produces traceable per-query and per-surface validation scores. Then add fixed-feature regression, rescaling, the remaining durations/protocols, and the wrong-support control.
4. Complete Steps 15–17 to evaluate and finish the planned Stage A study. Keep globally omitted conditions in a separately fitted experiment.
5. Begin Steps 18–22 when suitable force measurements are available. Begin Steps 23–25 only after their additional stage gates are met.

Every step gives an action, an output, and a completion checkpoint. The first complete pipeline is an engineering milestone; the full Stage A comparisons are needed to answer the plan's duration and probe-selection questions.

## Step 1. Define one primary scientific question

Write this in `docs/protocol.md`:

> How much short sliding-contact data is needed to predict a previously unseen surface's vibration response under another speed, direction, or nominal load? At the same contact-time budget, which second probe provides more information than repeating the first probe?

Define the terms:

| Term | Meaning in this study |
| --- | --- |
| Surface | One specimen ID in the dataset; not necessarily an entire material family |
| Support contact | A short measured contact the model may observe before predicting |
| Query condition | A requested speed, direction, and nominal load |
| Query response | The recorded vibration response hidden from prediction inputs |
| Unseen surface | A surface whose recordings were excluded from training and preprocessing-statistic fitting |
| Representation | A compact vector inferred from permitted support observations |
| Generalization | Prediction on held-out surfaces and explicitly identified held-out conditions |

Your initial target is **vibration spectral power**. Friction and compliance require additional evidence. The proposed encoder is a tool for answering the question, rather than the research contribution by itself.

Write the primary analysis cell explicitly, rather than leaving its budget or subset open to later selection:

| Field | Initial specification to freeze after the training/pilot audit |
| --- | --- |
| Condition experiment | New surfaces, familiar conditions |
| Support protocol and budget | `single`, 0.5 seconds at 40 mm/s, 0 degrees, 0.5 N |
| Query set | Common eligible conditions outside the union of all support conditions; repeat 1 |
| Comparison | Encoder/predictor versus nearest training-surface retrieval with the same held-out support |
| Metric and averaging | Raw log10 band-power MAE; mean over queries per surface, then mean over surfaces |
| Randomness and uncertainty | Average model initialization seeds within surface; paired surface/group bootstrap |

Use the longer durations and other methods as declared secondary analyses. For probe selection, predeclare direction versus repetition at two 0.5-second contacts as the main probe-choice contrast; report speed-versus-repetition and load-versus-repetition as well. The contrast measures prediction benefit from a fixed additional probe. It does not yet demonstrate adaptive probe selection, which would require a policy that chooses the next probe from the first observation and an independent evaluation of that policy.

Set a practical effect margin in log-power MAE units from training/pilot scales and repeat variability before opening test results. Record the scientific reason for that margin. Declare whether secondary comparisons are descriptive or use a specified multiplicity adjustment; isolated unadjusted intervals across many comparisons cannot establish every apparent benefit. Change initial choices only for documented audit findings and freeze them before test evaluation.

**Output:** `docs/protocol.md`, initially about one page.

**Checkpoint:** a reader can identify the observable inputs, hidden response, independent test units, primary comparison, and claim without seeing your code.

## Step 2. Read the closest papers and write the gap

Prioritize Heravi 2020/2024 and the Cluster documentation for Stage A. Read DiffTactile/TacTID before designing Stage B. ExSARN and HaptoFlow inform optional representations/renderers and need not delay the first pipeline. Read for these questions:

| Reference | Read for | Concrete note to produce |
| --- | --- | --- |
| Heravi et al., ICRA 2020 [R1] | Action-conditioned vibration prediction from tactile observations | List inputs, output, held-out setup, and similarities to your study |
| Heravi et al., IEEE Transactions on Haptics 2024 [R2] | Spectral prediction, rendering, and unseen-texture retrieval | Explain why retrieval is a necessary baseline |
| Cluster dataset paper and documentation [R3] | Acquisition, conditions, timing, and available labels | A data dictionary and limitations list |
| ExSARN, IROS 2021 [R4] | Compact tactile representation and sensor adaptation | What representation ideas you can use without assuming calibrated mechanics |
| HaptoFlow, 2026 [R5] | Interaction-conditioned vibrotactile generation | Why waveform generation is a later extension, after the first prediction study |
| DiffTactile, ICLR 2024 [R6] | Contact-parameter calibration and force-supervised simulation | What additional measurements enable the mechanical milestone |
| TacTID, 2024 [R7] | Friction and effective-stiffness inference | Existing mechanical inference methods and assumptions |

Create `docs/related_work.csv` with columns:

```text
paper,input_observations,conditioning,output,unseen_surface_test,
force_ground_truth,probe_budget_study,simulation_validation,
code_available,data_available,overlap_with_project,remaining_question
```

Use `unknown` when you have not verified a field. Record the page or section supporting each important entry. Check cited and citing papers around the closest works before making a novelty claim.

Heravi 2020 presents preliminary new-material embedding evidence; its main quantitative action/image tests use training materials. Heravi 2024 uses a nearest training representation for unseen textures. Your acceleration-support retrieval method adapts that idea to a different observation modality, so it is not an exact reproduction. [R1–R2]

Your candidate gap is a systematic, matched-budget investigation of brief moving probes and their information about response across conditions. A future extension tests whether that information supports calibrated sliding-force prediction. Treat this as a candidate contribution until a focused literature comparison supports it.

**Output:** the comparison table and a 150–250-word gap statement.

**Checkpoint:** you can explain how the experiment differs from action-conditioned rendering and from ordinary material classification, while acknowledging existing work.

## Step 3. Set up a reproducible workspace

Use Python 3.12 if available. Start on CPU; the first model is deliberately small. Install a PyTorch build suitable for your operating system from the [official installation instructions](https://pytorch.org/get-started/locally/). CUDA is optional.

Example Bash setup on Linux/macOS:

```bash
mkdir tactile-contact-research
cd tactile-contact-research
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy scipy pandas pyarrow openpyxl scikit-learn matplotlib pyyaml huggingface_hub jupyterlab
```

Equivalent PowerShell setup on Windows:

```powershell
New-Item -ItemType Directory -Path tactile-contact-research
Set-Location tactile-contact-research
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install numpy scipy pandas pyarrow openpyxl scikit-learn matplotlib pyyaml huggingface_hub jupyterlab
```

Install PyTorch separately using the official selector and the same environment's interpreter. Calling the interpreter directly avoids an activation dependency. Use `.\.venv\Scripts\python.exe` for subsequent Python commands on Windows; use the activated `python` on Linux/macOS.

Create directories with Python:

```python
from pathlib import Path

for name in [
    "configs", "docs", "notebooks", "scripts", "src/tactile_contact",
    "data/raw/cluster", "data/manifests", "data/features",
    "runs", "results/tables", "results/figures", "checks",
]:
    Path(name).mkdir(parents=True, exist_ok=True)
```

Record the environment after installation (use the virtual-environment interpreter on Windows):

```bash
python -m pip freeze > requirements.lock.txt
python --version
```

Suggested code contracts:

| File to create | Responsibility |
| --- | --- |
| `scripts/download_cluster.py` | Pin the dataset revision; download selected modalities/specimens |
| `scripts/build_manifest.py` | Enumerate files and record conditions and quality information |
| `scripts/audit_signals.py` | Produce synchronized plots and timing/quality summaries |
| `scripts/make_splits.py` | Build specimen-group-aware material splits |
| `scripts/build_features.py` | Select valid windows and cache spectral features |
| `scripts/build_episodes.py` | Construct fixed support/query records and enforce exclusions |
| `scripts/run_baselines.py` | Fit and score baseline methods without accessing test labels during fitting |
| `scripts/train_model.py` | Train a small model; choose checkpoints using validation data |
| `scripts/evaluate.py` | Score frozen predictors; write per-query and per-surface results |
| `scripts/make_figures.py` | Generate figures from saved numerical results |
| `src/tactile_contact/signal.py` | Signal preparation and PSD/band-power helpers |
| `src/tactile_contact/episodes.py` | Episode construction and feature access |
| `src/tactile_contact/models.py` | Encoder, pooling, and predictor |
| `src/tactile_contact/metrics.py` | Metrics, aggregation, and paired bootstrap |

A notebook is fine for the first plots. Move decisions and final computations into scripts or reusable functions before the locked evaluation.

**Output:** workspace, environment lock, and file-contract list.

**Checkpoint:** another environment can install the recorded dependencies and import your numerical packages.

## Step 4. Download a small, versioned data subset

Use the [Cluster Parquet mirror](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset). The documented naming convention is:

```text
sensor_data/accel/<surface_id>/<surface_id>_<direction>_<speed>_<force_mN>_<repeat>.parquet
```

Force and position use corresponding paths. Check the repository listing instead of assuming the layout remains unchanged.

The following starter script belongs in `scripts/download_cluster.py`. It downloads only a pilot subset and saves the revision. Its selected IDs are example audit specimens distributed across the published categories; verify the metadata and keep pilot specimens in the eventual training set.

```python
from pathlib import Path
import json
from huggingface_hub import HfApi, snapshot_download

REPO = "tamago117/cluster-haptic-texture-dataset"
SOURCE_FILE = Path("configs/data_source.json")
PILOT_IDS = [0, 38, 49, 65, 74, 79, 82, 87, 102, 103]
MODALITIES = ["accel", "force", "position"]

SOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)
api = HfApi(token=False)

if SOURCE_FILE.exists():
    source = json.loads(SOURCE_FILE.read_text())
    if source["repo_id"] != REPO or source.get("repo_type") != "dataset":
        raise ValueError("Saved source does not match the requested dataset")
    revision = source["revision"]
else:
    revision = api.repo_info(REPO, repo_type="dataset").sha
    if not revision:
        raise RuntimeError("Could not resolve a dataset revision")
    SOURCE_FILE.write_text(json.dumps({
        "repo_id": REPO,
        "repo_type": "dataset",
        "revision": revision,
        "pilot_ids": PILOT_IDS,
    }, indent=2))

files = api.list_repo_files(REPO, repo_type="dataset", revision=revision)
prefixes = [f"sensor_data/{m}/{i}/" for m in MODALITIES for i in PILOT_IDS]
selected = [p for p in files if any(p.startswith(s) for s in prefixes)]
if not selected:
    raise RuntimeError("Expected sensor directories were not found; inspect the listing")

print("Revision:", revision)
print("Selected sensor files:", len(selected))
print("Example paths:", selected[:5])

patterns = [f"{s}*.parquet" for s in prefixes]
patterns += ["texture_list.xlsx", "README.md"]
snapshot_download(
    repo_id=REPO,
    repo_type="dataset",
    revision=revision,
    allow_patterns=patterns,
    local_dir="data/raw/cluster",
    max_workers=4,
    token=False,
)
```

Run after copying the block:

```bash
python scripts/download_cluster.py
```

For the full study, expand the selected specimens to all IDs found in the metadata after the audit. Reuse the saved revision. Record each download selection separately from the original pilot list, so `configs/data_source.json` remains a truthful record of the pinned source and pilot. Download acceleration, force, and position; leave audio/images out of the first experiment.

Treat downloaded sensor records as immutable. Save transformations under `data/features`, and record hashes or a revision-backed file inventory. Check the original dataset's reuse terms before publishing redistributed data.

**Output:** raw pilot files and `configs/data_source.json`.

**Checkpoint:** you can load one acceleration, force, and position record for the same filename key. No unpinned update occurs when rerunning the download.

## Step 5. Build the recording and specimen manifests

Parse filenames; do not encode their material IDs as model inputs. Starter parser:

```python
from pathlib import Path
import re

RECORD_NAME = re.compile(
    r"^(?P<surface_id>\d+)_(?P<direction_deg>\d+)_(?P<speed_mm_s>\d+)_"
    r"(?P<force_mN>\d+)_(?P<repeat_id>\d+)\.parquet$"
)

def parse_record_name(path):
    match = RECORD_NAME.fullmatch(Path(path).name)
    if match is None:
        raise ValueError(f"Unrecognized sensor filename: {Path(path).name}")
    row = {k: int(v) for k, v in match.groupdict().items()}
    if row["direction_deg"] not in range(0, 360, 45):
        raise ValueError("Unexpected direction")
    if row["speed_mm_s"] not in [20, 30, 40, 50, 60]:
        raise ValueError("Unexpected speed")
    if row["force_mN"] not in [500, 1000]:
        raise ValueError("Unexpected nominal load")
    if row["repeat_id"] not in [0, 1]:
        raise ValueError("Unexpected repeat")
    row["nominal_force_N"] = row["force_mN"] / 1000.0
    row["recording_id"] = Path(path).stem
    return row
```

Create `data/manifests/recordings.csv` with one row per recording key:

```text
recording_id,surface_id,direction_deg,speed_mm_s,nominal_force_N,repeat_id,
accel_path,force_path,position_path,accel_rows,force_rows,position_rows,
start_ns,end_ns,missing_channels,nonfinite_values,time_reset,
steady_start_s,steady_end_s,usable_duration_s,qc_status,qc_reason
```

Read channel schemas directly. The mirror documents acceleration `time_ns,X,Y,Z` in g, force `time_ns,force` in newtons, and position `time_ns,X,Y` in millimeters. [R3]

Create `data/manifests/surfaces.csv`:

```text
surface_id,name,category,family_group,grouping_reason,pilot_surface,notes
```

Inspect `texture_list.xlsx` rather than guessing its column names. Group variants that clearly share a source, fabrication, or closely related specimen type where metadata justify this. Preserve a rationale; do not group everything in a broad category together automatically.

The complete published design has 80 distinct conditions per surface and two repetitions. Verify actual coverage rather than assuming every expected file is present. Cluster's specimen-level friction measurements use a separate slider/counterface and much slower motion; they are not synchronized tangential-force labels for these tactile scans. Do not train or score scan-force prediction as if they were. [R3]

**Output:** recording and surface manifests plus a missing-file summary.

**Checkpoint:** each modality's file maps to exactly one common recording key; IDs and conditions agree across channels.

## Step 6. Audit time alignment, contact quality, and usable motion

Load the three channels for each pilot recording. Retain integer nanosecond timestamps. If timestamps share a common origin, subtract one joint origin before converting to floating-point seconds:

```python
origin_ns = min(accel.time_ns.min(), force.time_ns.min(), position.time_ns.min())
accel_time_s = (accel.time_ns.to_numpy() - origin_ns) / 1e9
force_time_s = (force.time_ns.to_numpy() - origin_ns) / 1e9
position_time_s = (position.time_ns.to_numpy() - origin_ns) / 1e9
```

Do not subtract each channel's first timestamp independently; that can erase real offsets. Verify the common-clock interpretation using synchronized plots and acquisition documentation; inspect collection code if it is available. Sorting a record cannot repair a clock reset.

For each channel, record the mean and median sample interval, duplicate timestamps, gaps, interval variability, and duration. Acceleration is documented around 6 kHz; force is transmitted at 6 kHz but acquired at 80 Hz; position is around 100 Hz. Repeated force values do not constitute independent high-frequency force measurements. [R3]

Estimate sliding speed from smoothed position. A starting implementation smooths at the position channel's native rate and differentiates with respect to its actual time. Do not create new information by upsampling the position channel first.

Identify the longest contact interval with approximately steady nonzero speed. Initial candidate rules include: speed within `max(2 mm/s, 10% of nominal speed)`, nonzero normal contact, no timing reset, and finite values. Choose smoothing and gap thresholds from training/pilot records and publish them. Large load variation should be flagged for analysis; do not silently discard challenging surfaces to improve scores.

The author paper specifies 80 mm passes, giving about 1.33 seconds of nominal travel at 60 mm/s before considering transients. [R3] Audit whether a one-second **steady** query window is actually available at each speed. If that window excludes too many otherwise valid fast scans, choose a shorter fixed query duration, initially 0.5 seconds, using training/pilot data before locking the benchmark. Apply it to every query and method; do not shorten windows selectively after seeing errors.

Produce these plots for every pilot surface at several conditions:

1. Acceleration axes, force, and position/speed against the same time axis.
2. Nominal versus measured loading and its variation.
3. Acceleration spectra at different speeds, loads, and directions.
4. The two repetitions at identical conditions.

Decide and document the time interpretation for spectra. PC timestamps may include delivery jitter. If they accurately describe sampling intervals, interpolate within valid observed intervals onto a uniform grid; if they mainly describe serial delivery jitter, an acquisition-rate sample-index grid may be more appropriate. Compare these interpretations on pilot data. Inspect author acquisition code if available; the public repository contains processing/viewer code, and acquisition-code access has not been established. OS timestamps alone do not verify sensor acquisition timing. Record unresolved delivery delays and clock behavior, retain a time-base sensitivity analysis where relevant, and seek clarification if conclusions depend on absolute frequency precision. [R3] Do not extrapolate across missing intervals or beyond a recording.

**Output:** `docs/data_audit.md`, QC rules, and audit figures.

**Checkpoint:** you can explain the chosen fixed query duration and valid support durations, their loading variation, and the evidence for the selected spectral time base.

## Step 7. Lock material splits and eligible evaluation surfaces

Use approximately 80 training, 18 validation, and 20 test surfaces, allowing counts to change for justified specimen groups. Keep pilot specimens and related groups in training. Aim for useful category coverage without breaking family groups.

Create `data/manifests/split_materials.csv` with:

```text
surface_id,family_group,split,split_seed,reason
```

Mandatory assertions:

```python
assert set(train_ids).isdisjoint(val_ids)
assert set(train_ids).isdisjoint(test_ids)
assert set(val_ids).isdisjoint(test_ids)
assert set(train_groups).isdisjoint(val_groups)
assert set(train_groups).isdisjoint(test_groups)
assert set(val_groups).isdisjoint(test_groups)
```

Build splits before constructing overlapping windows or fitting normalization. Performance-driven selection of test specimens is prohibited by the experiment definition.

For matched duration and probe comparisons, define a common eligible cohort with all necessary support records valid at the longest compared duration. If one-second support is insufficient, revise the compared duration set using training/pilot coverage before evaluation; keep the same viable choices for every method. Report how the resulting cohort differs from the full dataset. Define a common query set using fixed QC rules. Record excluded specimens and reasons. Do not change the cohort for whichever model happens to perform poorly.

Lock three initialization seeds, initially `[0, 1, 2]`. Choose whether later robustness checks use additional predeclared material splits. Record that choice before the main test evaluation.

**Output:** split manifest, eligibility manifest, and a protocol revision with the evaluation cohort.

**Checkpoint:** a specimen group never crosses splits; every compared protocol is scored on the same eligible cohort and query conditions.

## Step 8. Extract support and query windows

For each valid steady interval, define the valid start once and extract nested 0.25-, 0.5-, and 1-second support windows from that start. The shorter observation must be the prefix of the longer observation. This compares increasing observed steady-contact time at one start location. The steady interval and its start are selected retrospectively using frozen QC rules on the complete recording, so this benchmark does not validate online contact-onset detection. Centered windows are an optional sensitivity analysis with a different spatial sampling pattern.

Identify support onset using motion/contact metadata and fixed rules rather than acceleration amplitude or later prediction errors. The reference experiment assumes established steady sliding; approach, stabilization, and repositioning time are outside its observation budget. A future online experiment must use a causal onset rule, count detection/stabilization overhead, and avoid future samples in smoothing or window selection.

Use the fixed query duration chosen in Step 6, initially one second. The observed support and hidden query must belong to different condition recordings. Do not extract both from overlapping pieces of one scan for the main cross-condition result.

Training may sample different starts within allowed steady intervals as augmentation. Validation and test starts are fixed, with longer durations sharing the same start. Save each selected window's start/end times and a unique `window_id`.

Each window manifest row should include:

```text
window_id,recording_id,surface_id,split,role,duration_s,
start_s,end_s,speed_mm_s,direction_deg,nominal_force_N,
measured_support_force_mean_N,measured_support_force_std_N,feature_path,
window_config_hash,time_base_id
```

Actual force summaries are permitted only from the observed support when used as inputs. Store query force for QC and separate diagnostic analyses; the normal prediction interface does not receive future measured query force. Query-window QC is an offline definition of the recorded evaluation target, using frozen rules. It does not show that a deployed predictor can select future valid windows or know the future force. Keep QC metadata separate from prediction tensors, and report the fraction of conditions that pass.

Before spectral extraction, produce a uniform acceleration array according to the timing decision in Step 6. If reducing the sampling rate, apply a documented anti-alias filter before decimation; interpolation alone is not an anti-alias filter. Preserve the source-frequency range needed by the full-PSD rescaling baseline as well as the modeled query band. Keep acceleration in consistent units; the starter helper below converts g to meters per second squared. Do not normalize each contact to unit variance.

At the selected sampling rate, extract exactly `round(duration_s * fs)` samples per window. If using timestamp interpolation, construct that many uniformly spaced sample times and require the entire grid to lie within a valid observed interval. If using acquisition-rate indices, select the corresponding contiguous sample count. This avoids accidentally extracting 1499 rather than 1500 samples for a nominal 0.25-second contact.

**Output:** deterministic evaluation windows and training-window rules.

**Checkpoint:** every result can be traced to raw records and exact intervals; shorter support observations are prefixes of the longer contact at the same start.

## Step 9. Implement spectral features with physical amplitude preserved

Starter settings: sampling rate 6000 Hz after the documented time-base handling; Welch segments of 0.125 seconds; 50% overlap; 32 linear bands from 24 to 1000 Hz. These settings avoid empty narrow low-frequency bands at the starter spectral resolution. Verify the range against the real signal and sensor noise before freezing it.

Cache both the full PSD and 32 band powers. The full PSD supports a stronger speed-rescaling baseline without requiring another contact. The encoder can initially use the compact bands, with a dense-spectrum input ablation if compression proves limiting.

Put this function in `src/tactile_contact/signal.py`:

```python
import numpy as np
from scipy.signal import welch

def spectral_features(accel_g, fs=6000.0, floor=1e-10):
    """Uniformly sampled acceleration, shape (samples, 3), in g.

    Return full PSD and 32x3 band powers/log10 powers.
    Band-power units: (m/s^2)^2. Log floor has those same units.
    """
    a = np.asarray(accel_g, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] != 3 or not np.isfinite(a).all():
        raise ValueError("Expected a finite samples-by-3 acceleration array")
    if not np.isfinite(fs) or fs <= 2000:
        raise ValueError("Sampling rate must place 1000 Hz strictly below Nyquist")
    nperseg = int(round(0.125 * fs))
    if len(a) < 2 * nperseg:
        raise ValueError("Window is shorter than the starter minimum of 0.25 s")
    if not np.isfinite(floor) or floor <= 0:
        raise ValueError("Power floor must be finite and positive")
    a = a * 9.80665
    a = a - a.mean(axis=0, keepdims=True)
    frequency_hz, psd = welch(
        a, fs=fs, window="hann", nperseg=nperseg,
        noverlap=nperseg // 2, detrend=False,
        scaling="density", axis=0,
    )
    edges = np.linspace(24.0, 1000.0, 33)
    df = frequency_hz[1] - frequency_hz[0]
    band_power = np.empty((32, 3), dtype=np.float64)
    for j, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (frequency_hz >= lo) & (
            (frequency_hz <= hi) if j == 31 else (frequency_hz < hi)
        )
        if not mask.any():
            raise ValueError("Empty frequency band; revise the spectral settings")
        band_power[j] = psd[mask].sum(axis=0) * df
    log_band_power = np.log10(band_power + floor)
    rms_by_axis = np.sqrt(band_power.sum(axis=0))
    return {
        "frequency_hz": frequency_hz,
        "psd": psd,
        "band_edges_hz": edges,
        "band_power": band_power,
        "log_band_power": log_band_power,
        "rms_by_axis": rms_by_axis,
        "floor": float(floor),
    }
```

The helper uses rectangular sums over PSD-bin centers, assigning each bin to exactly one band; the final band includes the 1000 Hz bin. Save the actual frequency grid and per-band bin counts as well as the nominal edges. This is a discrete spectral convention, with small differences from exact continuous band-edge integration. Use the same convention in targets, rescaled spectra, and RMS reconstruction; changing integration rules requires regenerating every feature and result.

Flatten `log_band_power` in band-major order: band 0 X/Y/Z, then band 1 X/Y/Z, and so on. Input and output dimensions are initially 96. Preserve this ordering in caches and checkpoints.

The suggested floor is an initial numerical setting, not a measured sensor-noise floor. Review it against training-data magnitudes and lock it before evaluation. Report sensitivity if substantial portions of the signal are floor-limited.

Before using the helper on real data, verify with a synthetic sinusoid: the peak is near its input frequency; doubling amplitude multiplies power by four; the corresponding log10 power difference is about 0.60206; adding a constant offset does not alter the spectrum after demeaning. Also check approximate agreement between integrated in-range power and waveform variance when the synthetic signal lies within the modeled range.

**Output:** feature cache, feature configuration, and numerical verification notes.

**Checkpoint:** all durations produce finite 96-dimensional vectors with preserved amplitude, and spectral settings are identical across compared protocols.

## Step 10. Fit preprocessing using training surfaces only

Fit a feature scaler on permitted training support windows. Use a declared balanced sample across training surfaces, protocols, and durations; repeated episode references to one cached window must not change its statistical weight. For each spectral feature, save its training mean and standard deviation. Replace a near-zero standard deviation with 1 rather than amplifying a constant feature. Apply the saved scaler unchanged to validation/test support.

For the first model, keep query targets in raw log10 band-power units and train with mean absolute error in those units. This keeps training loss aligned with the primary reported metric. If you later standardize targets, fit that scaler on training targets only and invert it before reporting metrics.

Encode conditions explicitly:

```python
import numpy as np

def condition_vector(speed_mm_s, direction_deg, nominal_force_N):
    theta = np.deg2rad(direction_deg)
    return np.array([
        speed_mm_s / 40.0,
        np.cos(theta),
        np.sin(theta),
        nominal_force_N / 0.5,
    ], dtype=np.float32)
```

The periodic angle encoding avoids an artificial discontinuity between 0 and 315 degrees. It encodes the dataset's direction convention; do not use it to infer a world-coordinate velocity vector without checking that convention against position.

One default support vector contains:

```text
96 standardized log-band powers
4 observed condition features
1 observed duration / 1 second
= 101 input features per support contact
```

The query vector contains four requested condition features. An optional experiment adds two support-force statistics, changing support dimension to 103. Evaluate that addition separately; the future measured query force remains excluded.

For the globally omitted-speed experiment, rebuild the scaler from allowed training speeds only. A scaler fitted using 30/50 mm/s data would contaminate that experiment even if the neural-network training omitted those speeds.

**Output:** `data/features/scaler.npz`, feature order, and configuration hash.

**Checkpoint:** every transformation has a recorded training-only fit source, and the query target stays outside the model-input builder.

## Step 11. Build support/query episodes explicitly

Use these fixed support protocols, with `r0` denoting repeat 0:

| Protocol | Support conditions `(speed, direction, force, repeat)` |
| --- | --- |
| `single` | `(40, 0, 0.5, r0)` |
| `repeat` | `(40, 0, 0.5, r0)` and `(40, 0, 0.5, r1)` |
| `speed` | `(40, 0, 0.5, r0)` and `(20, 0, 0.5, r0)` |
| `load` | `(40, 0, 0.5, r0)` and `(40, 0, 1.0, r0)` |
| `direction` | `(40, 0, 0.5, r0)` and `(40, 90, 0.5, r0)` |

Exclude the following condition triples from the common query set for **every** protocol:

```python
FORBIDDEN_QUERY_CONDITIONS = {
    (40, 0, 0.5),
    (20, 0, 0.5),
    (40, 0, 1.0),
    (40, 90, 0.5),
}
```

The fully observed condition grid contains 80 triples, so a complete primary query grid has 76 triples before QC exclusions. Use repeat 1 for the fixed validation/test primary query response. Training may sample query repeat 0 or 1 outside the forbidden condition union, giving every fitted method access to the same allowed training response pool. A predeclared reverse-repeat check swaps repeat assignments consistently and is reported separately. The repeat-control protocol observes both reference repeats, but that reference condition is excluded from all queries.

Distinguish **per-contact duration** from **total observed time**. The second-probe comparison uses two contacts of equal duration for every two-probe protocol. To compare one versus two contacts at equal total time, score `single` at 1 second against each two-probe protocol at 0.5 seconds per contact; similarly compare 0.5 seconds against two 0.25-second contacts. Keep the cohort and queries identical. Record observed sliding distance as well: equal time at different speeds does not mean equal traversed area. Repositioning time is not represented in this dataset, so these are observation-budget comparisons rather than complete robot execution-time comparisons.

Episode schema:

```text
episode_id,surface_id,split,protocol,duration_s,
support_window_ids,query_window_id,query_speed_mm_s,
query_direction_deg,query_nominal_force_N,
total_support_time_s,total_support_distance_mm,condition_subset
```

For every episode, assert:

- Support and query belong to the same surface within the correct material split.
- All support windows match the allowed protocol and duration.
- No support window or recording ID equals the query's.
- Query condition is outside the union of observed support conditions.
- Actual observation time is accounted for; no hidden extra repetitions are averaged into a test support feature.
- The prediction input includes support measurements, their conditions, and requested query conditions only.

Maintain two access functions: `make_prediction_inputs(episode)` returns support and query-condition tensors; `get_target(episode)` returns the hidden query response for training loss or scoring. This separation makes accidental target access easier to notice.

For training, sample surfaces uniformly, then a protocol and duration uniformly, then an allowed query condition. Randomize training support/query starts only within their saved valid intervals. Define an epoch as a fixed number of episodes per surface, initially 64; this balances materials rather than allowing long scans to dominate.

For validation/test, store a fixed episode list. Use all common eligible queries and identical episode ordering for all methods. Cache targets once rather than letting each predictor rebuild its own favorable evaluation set.

**Output:** train episode rules and fixed validation/test episode manifests.

**Checkpoint:** substituting a prediction implementation cannot change the evaluation samples or reveal query measurements.

## Step 12. Implement the baselines before the encoder

### Baseline A: requested conditions only

Fit a small regression model from the four query-condition features to the 96-dimensional query log spectrum, using training episodes. This estimates the average response of training surfaces. It receives no test surface observation.

Use a ridge regression first; if helpful, also use a small conditions-only MLP with the same training/validation rules as the proposed model.

### Baseline B: reuse the observed spectrum

For one probe, return its log spectrum. For two probes, average their **linear band powers** and then take the log. Averaging logarithms instead would be a different baseline and should be labeled as such.

This method ignores query conditions. Its purpose is to establish whether prediction improves beyond copying the measurement.

### Baseline C: rescale the observed spectrum by speed

Keep the support's full PSD from Step 9. With speed ratio `s = query_speed / support_speed` and nominal-load ratio `r = query_load / support_load`, use the proposed approximation:

\[
\hat S_q(f)=s^{p-1}r^{b}S_s(f/s).
\]

Here `p` is a power-scaling exponent and `b` is a load-scaling exponent. They are fitted on training pairs and checked on validation surfaces. The factor `1/s` accounts for frequency-axis stretching; a simple geometric acceleration model suggests an illustrative `p=4`, but the apparatus response may not obey that idealization. Do not assume that exponent is empirically correct.

Implement interpolation of `S_s(f/s)`, then integrate over the same target bands. Reject unsupported frequency extrapolation or report it explicitly. With the starter query band up to 1000 Hz and this dataset's speed ratios, retaining the full 6 kHz-sampled support PSD provides the needed source-frequency range, subject to the data audit confirming its validity.

Fit exponents using training observations; choose among fitted candidates using validation surfaces. Never optimize them on test spectra. Freeze the following rule so the baseline returns predictions for the complete primary grid: choose the support with the smallest circular angular difference to the query, break ties by the smallest absolute log speed ratio, then by its canonical protocol order. Rescale that support PSD and ignore any remaining angular mismatch. Label this the direction-agnostic rescaling baseline; it cannot model directional variation.

Also report a same-direction diagnostic subset, where the selected support and query directions match exactly. Score every compared method on that same subset, and give its condition/specimen count. This subset does not replace the common-grid primary evaluation.

This dense-PSD baseline has access to the same raw support contacts but a less compressed signal representation. Label it accordingly. If it dominates the compact encoder, test whether compression caused the failure before attributing it to learning itself.

### Baseline D: nearest training-surface retrieval

For each training surface, build a fingerprint under each allowed support protocol/duration. Use the same feature definitions as the test support. For the primary retrieval baseline, construct the training fingerprint from exactly the protocol-prescribed support records and duration, in a fixed contact order. Flatten the standardized spectral support features and use Euclidean distance; the common condition/duration fields are fixed within a library and need not affect its distance. In the optional force-summary experiment, append the same permitted force summaries with training-only scaling to retrieval and fixed-feature regression, so additional information is available to each comparison method. The library never uses held-out-surface queries. A repeat-averaged fingerprint is a separately labeled stronger-library check with its additional offline calibration disclosed.

At inference:

1. Compute the unfamiliar surface's fingerprint from its allowed support only.
2. Find the nearest training fingerprint using training-fitted feature scaling.
3. Retrieve that training surface's spectrum at the requested condition. Default to both permitted training repeats: average linear band powers, then take `log10(power + floor)`. Training response records are offline calibration, distinct from the held-out surface's brief-support budget. Make the same training-record pool available to all fitted methods. Save the exact source records and aggregation.

For the globally omitted-speed experiment, **do not retrieve the training surface's recorded 30/50 mm/s response**. Those labels are omitted from that entire experiment. Instead interpolate from permitted 20/40/60 mm/s spectra using a declared rule, initially linear interpolation of log band power.

Restrict each library to training surfaces with valid fingerprints and the required response coverage, using fixed QC rules; report its size. Break equal distances by a fixed sorted training ID. Never put validation or test surfaces in the retrieval library. Save the retrieved training ID as a diagnostic, not a prediction input to the learned model.

### Baseline E: measured features plus regression

Use the mean and standard deviation of permitted support vectors, probe count, requested conditions, and optional support-by-query interaction features. Fit a regularized multi-output regression. Choose its regularization on validation surfaces.

This asks whether a learned bottleneck provides value beyond ordinary spectral features.

### Control: wrong-surface support

Replace a test surface's support with another test surface's support at the same protocol/duration, while keeping requested query conditions and hidden target unchanged. Substitute all support fields together, including any measured support-force summaries. No wrong surface's query measurements are exposed. Use a fixed derangement with no self-matches. Keep this mapping identical across model seeds.

An optional harder control swaps within category when enough held-out specimens exist. Label the eligible subset and report it separately.

**Output:** predictions from every baseline and control, on the same episodes.

**Checkpoint:** each baseline uses only permitted inputs; nearest retrieval never reads omitted-speed labels or a held-out surface's response.

## Step 13. Implement the small encoder and predictor

Use one model trained across the declared one- and two-probe protocols and durations. This holds network capacity constant when comparing probe choices. If you instead train separate models, report that design and match training budgets.

Default tensors:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `support` | `[batch, 2, 101]` | Up to two support contacts; padded slots are masked |
| `support_mask` | `[batch, 2]` | 1 for an observed contact, 0 for padding |
| `query_condition` | `[batch, 4]` | Requested speed, angle encoding, nominal load |
| `target_log_power` | `[batch, 96]` | Hidden query log10 band powers |
| `z` | `[batch, 16]` | Pooled inferred representation |

Starter code for `src/tactile_contact/models.py`:

```python
import torch
from torch import nn

class ContactPredictor(nn.Module):
    def __init__(self, support_dim=101, output_dim=96, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(support_dim, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, latent_dim),
        )
        self.predictor = nn.Sequential(
            nn.Linear(latent_dim + 4 + 1, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, output_dim),
        )

    def forward(self, support, support_mask, query_condition):
        if support.ndim != 3 or support.shape[-1] != self.encoder[0].in_features:
            raise ValueError("Expected [batch, slots, support_dim]")
        if support_mask.shape != support.shape[:2]:
            raise ValueError("Support mask must match batch and slots")
        if query_condition.shape != (support.shape[0], 4):
            raise ValueError("Expected four query-condition features per episode")
        if not torch.all((support_mask == 0) | (support_mask == 1)):
            raise ValueError("Support mask must contain only zero or one")
        if not torch.isfinite(support).all() or not torch.isfinite(query_condition).all():
            raise ValueError("Inputs must be finite; use finite zero padding")
        mask = support_mask.to(device=support.device, dtype=support.dtype)
        count = mask.sum(dim=1, keepdim=True)
        if torch.any(count <= 0):
            raise ValueError("Every episode needs at least one support contact")
        encoded = self.encoder(support)
        z = (encoded * mask.unsqueeze(-1)).sum(dim=1) / count
        context = torch.cat([z, query_condition, count / 2.0], dim=1)
        return self.predictor(context), z
```

Use finite zero padding; multiplying an encoded NaN by a zero mask would still propagate NaN. Mean pooling makes the support-set representation invariant to probe order. The encoder sees each observation's condition, so speed/load-dependent changes can be interpreted. Probe count is explicit rather than hidden in zero padding.

Starter training choices: Adam at `1e-3`, batch size 128, at most 60 epochs, gradient-norm clipping at 1, and early stopping after 10 epochs without improved **validation per-surface raw log-power MAE**. Use training-only sampling, the same three initialization seeds, and a fixed validation episode manifest. For checkpoint selection, first average queries per surface in each protocol/duration cell, then average surfaces, then give each declared cell equal weight. Save both that aggregate and the primary-cell validation score. A large query subset must not dominate selection merely because it has more rows. These are starting choices, not optimized results.

Minimal training-step example:

```python
model.train()
optimizer.zero_grad(set_to_none=True)
prediction, _ = model(support, support_mask, query_condition)
loss = torch.nn.functional.l1_loss(prediction, target_log_power)
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
optimizer.step()
```

Use `model.eval()` and `torch.no_grad()` for validation/test. Save model weights, feature/scaler configuration, split and episode hashes, initialization seed, optimizer settings, selected epoch, and environment information together.

Before real training, set Python, NumPy, and PyTorch seeds. If using CUDA, document device and deterministic settings; fixed seeds alone do not establish identical results across hardware or library versions. Do not claim more reproducibility than you measured.

**Output:** training script, checkpoint format, and one trained development checkpoint.

**Checkpoint:** the model accepts both one and two masked probes, returns 96 outputs, and has no material-ID or future-query-measurement input.

## Step 14. Perform engineering checks before scientific evaluation

Run these meaningful checks:

1. **Numerical spectrum check:** amplitude doubling changes power fourfold and log10 power by about 0.60206.
2. **Split check:** training, validation, and test material/family sets are disjoint.
3. **Episode check:** no common query condition appears in the support-condition union.
4. **Mask check:** changing a padded support slot does not change prediction; swapping two observed slots preserves prediction.
5. **Tiny training check:** a small model can fit a few training episodes with different targets. Failure suggests code, scaling, or optimization problems.
6. **Prediction-input check:** two calls with identical permitted inputs produce identical outputs in evaluation mode, regardless of attached target fields.
7. **Retrieval check:** every retrieved ID belongs to the training set and its output came from allowed condition labels.

The tiny fit is a debugging result, not evidence of generalization. Keep debugging figures separate from research result figures.

If the network only predicts a mean spectrum, inspect gradient flow, loss scale, query conditioning, support masking, and sampling before changing architecture. If force or timing QC excludes many records, inspect the exclusion rules before trusting the benchmark cohort.

**Output:** `docs/implementation_checks.md` and relevant numerical/assertion results.

**Checkpoint:** you have eliminated basic implementation and leakage failures without using test outcomes to redesign the model.

## Step 15. Freeze choices using validation data, then run the test

Use validation data for a small, recorded set of choices: latent sizes 8/16/32 if necessary, regularization, spectral floor/range after audit, and optional measured support-force inputs. Record every attempted configuration and why it was retained or rejected.

Keep model selection modest. An elaborate model search would change this into an architecture-optimization project without necessarily improving the scientific question.

Before testing, freeze:

```text
dataset revision and raw-data inventory
QC rules and window/time-base configuration
material split and specimen grouping
eligible comparison cohort and episode manifests
feature/scaler definitions and spectral floor
baseline definitions and fitted choices
model configuration and validation-selected checkpoints
primary analysis cell, metric, comparison, and aggregation rules
practical effect margin and secondary-comparison/multiplicity policy
load/direction subgroup definitions and predictive-uncertainty plan, if used
```

Run the frozen test once as the main evaluation, then only predeclared robustness checks. If a genuine implementation bug is found, document it, fix it, and rerun all affected methods consistently; label the revised evaluation. Do not change architecture or QC to rescue a disappointing score.

Separate two condition experiments:

| Experiment | Training/validation speeds | Test query speeds | Main interpretation |
| --- | --- | --- | --- |
| Familiar conditions | 20/30/40/50/60 | All allowed common-grid speeds | Generalization to new surfaces |
| Speed interpolation | 20/40/60 only | 30/50 | New surfaces and globally omitted intermediate speeds |

For both experiments, the support protocols use only 20/40 mm/s. Omitted 30/50 mm/s recordings never enter model fitting, preprocessing statistics, exponent fitting, or retrieval outputs in the interpolation experiment.

Evaluate load transfer and direction transfer as named subsets of the fixed query set. Define unobserved-load transfer as 1 N queries for protocols whose supports all use 0.5 N (`single`, `repeat`, `speed`, `direction`). Report `load` separately as observing both loads. Define unobserved-direction queries per protocol as directions absent from its support set; use their intersection when comparing protocols on a matched angular subset. Publish the exact condition lists and surface counts. A one-load support protocol predicting 1 N tests unobserved-load transfer. A two-load support protocol tests the benefit of observing both loads; do not describe it as predicting a completely unobserved load.

**Output:** frozen configuration bundle and raw prediction tables for three seeds.

**Checkpoint:** a test result identifies its exact material split, support budget, condition experiment, and permitted input interface.

## Step 16. Compute metrics and confidence intervals correctly

Save one row per query:

```text
experiment,model,seed,episode_id,surface_id,family_group,protocol,duration_s,
query_speed_mm_s,query_direction_deg,query_nominal_force_N,
log_power_mae,rms_error_X,rms_error_Y,rms_error_Z,total_rms_error,
retrieved_training_id,checkpoint_id,config_hash
```

Primary error for a query is the mean absolute difference across its 96 log10 band-power entries. First average over query conditions within a surface, then average across surfaces. This prevents surfaces with more valid windows from dominating.

Recover modeled-band amplitude from spectra:

```python
import numpy as np

def rms_from_log_power(log_power, floor=1e-10):
    log_power = np.asarray(log_power, dtype=np.float64).reshape(-1, 32, 3)
    linear_power = np.maximum(np.power(10.0, log_power) - floor, 0.0)
    rms_axes = np.sqrt(linear_power.sum(axis=1))
    rms_total = np.sqrt(linear_power.sum(axis=(1, 2)))
    return rms_axes, rms_total
```

Keep this metric limited to the modeled frequency band. Do not call it total physical acceleration RMS over frequencies you did not predict. Use absolute amplitude errors as primary amplitude diagnostics; relative errors need a documented denominator floor near zero.

Compare methods using paired surface errors, averaging initialization seeds within each surface for the main paired comparison and reporting seed variation separately. Treat specimen families as bootstrap clusters where appropriate. Supply homogeneous, nonmissing group IDs from the frozen manifest. The helper resamples whole families and retains a surface-weighted mean within each draw; large families contain more surfaces and therefore more weight. Use a different, predeclared estimator if the question calls for equal weight per family.

Starter bootstrap helper for `src/tactile_contact/metrics.py`:

```python
import numpy as np

def paired_bootstrap(baseline_error, proposed_error, group_ids=None,
                     draws=10000, seed=7):
    a = np.asarray(baseline_error, dtype=np.float64)
    b = np.asarray(proposed_error, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or len(a) == 0:
        raise ValueError("Need matching nonempty per-surface error arrays")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Nonfinite errors")
    if not isinstance(draws, (int, np.integer)) or draws < 1:
        raise ValueError("draws must be a positive integer")
    groups = (np.arange(len(a), dtype=object) if group_ids is None
              else np.asarray(group_ids, dtype=object))
    if groups.shape != a.shape:
        raise ValueError("Group IDs must align with surfaces")
    def valid_group_id(g):
        if g is None:
            return False
        if isinstance(g, (str, np.str_)):
            return bool(g.strip())
        if isinstance(g, (int, float, np.integer, np.floating)):
            return bool(np.isfinite(g))
        return False
    if not all(valid_group_id(g) for g in groups):
        raise ValueError("Group IDs must be nonmissing scalar strings or numbers")
    string_ids = all(isinstance(g, (str, np.str_)) for g in groups)
    numeric_ids = all(isinstance(g, (int, float, np.integer, np.floating)) for g in groups)
    if not (string_ids or numeric_ids):
        raise ValueError("Use homogeneous string or numeric group IDs")
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == g) for g in unique]
    delta = a - b  # positive means lower error for the proposed method
    rng = np.random.default_rng(seed)
    boot = np.empty(draws)
    for i in range(draws):
        chosen = rng.integers(0, len(members), size=len(members))
        indices = np.concatenate([members[j] for j in chosen])
        boot[i] = delta[indices].mean()
    return {
        "mean_improvement": float(delta.mean()),
        "ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "surfaces": len(a),
        "independent_groups": len(unique),
    }
```

An interval spanning zero is inconclusive about the sign of the mean improvement under this analysis: it does not establish equivalence. Claim a practically meaningful improvement only when the interval supports the predeclared positive effect margin. Claim practical equivalence only with a specified equivalence procedure and margin; otherwise report that this evaluation has not demonstrated an advantage. A statistically clear small effect can still fall below the intended use's needs.

Report absolute paired improvement in log10-power MAE units, its interval, and independent group count. Percent error reduction is optional and unstable when baseline error is near zero. A log-power difference describes a ratio of band powers; it is not directly a force or motion improvement. Bootstrap intervals condition on this split and library, and a small number of independent groups limits their precision.

These intervals concern mean method differences. If predictive uncertainty for individual responses is added, fit/calibrate it using training/validation groups and evaluate coverage and interval width on held-out surfaces. Ensemble disagreement alone does not establish calibrated prediction uncertainty.

Two repetitions provide only limited information about repeatability. Use their differences as context, not a precise irreducible-error estimate. Additional windows from a repetition are correlated observations rather than extra independent specimens.

**Output:** per-query/per-surface tables, paired improvements, bootstrap intervals, and seed variability.

**Checkpoint:** the reported sample size reflects independent surfaces/groups; all methods are compared on aligned samples.

## Step 17. Make figures, interpret failures, and finish the public study

Required figures:

1. Paired support/query panels, each with synchronized acceleration, force, and motion channels and the selected window marked.
2. Predicted and measured spectra for successes and failures, using the same selection rule for all models.
3. Error versus support duration.
4. Two-probe error by second-probe type, with the repetition control.
5. Error by query speed, nominal load, and direction.
6. Paired per-surface improvement over retrieval; show the full distribution.
7. Correct-support versus wrong-support performance.
8. Repeated-recording differences as limited repeatability context.

Use plots generated from saved tables, rather than manually selected notebook states. Include specimen counts and confidence-interval units in captions. Example selection should be reproducible, such as median, best, and worst surface by a predeclared metric—not a collection of attractive predictions.

Interpretation rules:

| Observation | Defensible interpretation | Next action |
| --- | --- | --- |
| Wrong support performs similarly | Model has not demonstrated useful surface-specific conditioning | Inspect apparatus/condition signals and inference bottleneck |
| Paired retrieval/model difference is inconclusive | This evaluation has not demonstrated an advantage for the learned embedding; equivalence requires its own margin/test | Report it; examine input compression and probe information |
| Perpendicular probe beats repetition at equal time | The orthogonal contact adds useful observations under this acquisition protocol | Examine anisotropy, spatial path differences, and surface heterogeneity |
| Load probe helps while one-load transfer fails | One observed load does not adequately constrain loading response | Audit actual load variation; measure more loads later |
| Spectra improve but amplitudes remain wrong | Shape similarity is insufficient for physically scaled response | Inspect normalization, floors, and force dependence |
| All methods are poor and repeats disagree strongly | Target variability or measurement limits may dominate | Revisit the prediction target and need for more independent trials |

Direction changes can alter the scanned path and surface patch as well as heading. Equal time and recorded distance do not isolate intrinsic anisotropy; use position metadata to characterize coverage and preserve these alternatives in the conclusion.

Write a short report with: question, related work, data/protocol, baselines/method, results, ablations/failures, limitations, and mechanical extension. A 6–8-page main report plus appendix is a practical target, not an admissions requirement.

Use an accurate title, initially **Brief Contact Probes for Predicting Texture Responses Across Interaction Conditions**. Describe the completed work as an independent tactile-response study. Include mechanical identification and robot learning as future work until those experiments are completed.

**Stage A completion gate:** save the primary paired comparison, duration curves, all declared second-probe contrasts, wrong-support result, load/direction subsets, the separately fitted omitted-speed experiment, exclusions, and repeatability context. Package them with the report and code. If data coverage prevents a planned contrast, explain that limitation and narrow the answered question. A simple baseline winning is a valid completed result.

**Output:** report, figures, configurations, code, and a concise completed-work description.

**Checkpoint:** you can answer what was learned, which alternative explanations were tested, and what remains unresolved, even if a simple method won.

## Step 18. Decide whether the mechanical milestone is currently feasible

While completing the public study, ask a potential mentor or partner about an existing calibrated contact rig. Provide your one-page protocol and preliminary figures. Identify actual capabilities rather than assuming a tactile kit includes independent force ground truth.

Required measurements/capabilities:

| Requirement | Why it is needed |
| --- | --- |
| Normal force independent of the tactile estimator | Loading ground truth and force-ratio calibration |
| Tangential force independent of the tactile estimator | Sliding resistance ground truth |
| Known probe geometry and counterface | Defines the physical contact being identified |
| Controlled relative motion | Separates material/contact effects from changing actions |
| Position and velocity measurements | Motion alignment and confirmation of sliding |
| Tactile signal or probe acceleration | Observation input and connection to Stage A |
| Repeatable mounting and timestamps | Calibration and repeatability |

A linear stage or repeatable planar fixture can be enough. A robotic hand is not necessary. Choose hardware only after defining the required force range, sensitivity, timing, and fixture arrangement.

If using a public force dataset, verify downloadable raw force/motion channels, timestamps, probe geometry, condition variation, and sufficient independent surface specimens. DiffTactile's paper and code are relevant, but described real recordings should not be treated as available until access is verified. Two surfaces can support a calibration demonstration, not a broad unseen-material claim.

If access remains unavailable, complete the public report and describe mechanics as the next experimental milestone. A simulation-only identification study can be added and labeled as simulation-only; it does not replace real validation.

**Output:** `docs/mechanics_access.md` with available measurements, missing capabilities, and the chosen scope.

**Checkpoint:** you can identify which device produces each ground-truth quantity and which measurements are actually obtainable.

## Step 19. Calibrate the force-and-motion measurement chain

Start with rigid flat surfaces and a fixed probe. Keep geometry, mounting, and orientation unchanged during the pilot. Record the probe material and dimensions.

Perform these engineering measurements before collecting research trials:

1. Zero force readings with no contact and estimate offset drift.
2. Apply known normal loads across the intended range and fit/check the calibration.
3. Apply known tangential loads and check calibration and normal/tangential cross-axis coupling.
4. Verify force signs and coordinate transforms with known directional motion.
5. Measure fixture/guide drag independently where it can influence tangential force.
6. Verify encoder scale and actual motion against an independent length reference if needed.
7. Check temporal offsets using an event observable in both motion/tactile and force channels.
8. Repeat a reference contact before and after sessions to measure drift.

Choose operating loads that produce sliding forces clearly above effective measurement uncertainty. If a predicted improvement is smaller than calibration error or repeat variability, the rig cannot convincingly establish it.

Store `configs/calibration.json` with units, coefficients, uncertainties, signs, transforms, offsets, date, instrument IDs, probe ID, and mounting/session IDs. Raw readings remain unchanged; calibrated data are a derived product.

For compliance later, also characterize deformation in the probe, fixture, and mounting. Force divided by actuator travel is not automatically the surface's stiffness.

**Output:** calibration report, reference trials, and a documented operating range.

**Checkpoint:** the measured force differences of interest exceed the instrument/fixture uncertainty and calibration is repeatable across sessions.

## Step 20. Collect a small randomized sliding-contact pilot

Starting proposal: 8–12 distinct surface specimens, three usable speeds, three nominal loads, and five independent repetitions per condition. At ten surfaces this is 450 trials. Repeated windows from a single trial do not count as those repetitions.

Select speeds and loads within the calibrated rig's operating range. Keep initial sliding direction fixed. This first mechanical question concerns speed/load dependence; add directional friction in a later expansion.

Distribute repetitions across at least two sessions when feasible. Randomize trial order within practical blocks, record cleaning/replacement procedures, and include reference trials to distinguish surface effects from drift or wear.

Each trial should include approach, contact establishment, steady sliding, and release. Record enough steady contact for permitted support intervals and separate query trials. Identify continuous sliding from measured relative motion; do not infer kinetic friction from arbitrary sticking contacts.

Save one synchronized derived table per trial:

```text
time_s,position_x_m,position_z_m,velocity_x_m_s,
commanded_velocity_x_m_s,commanded_normal_force_N,
measured_normal_force_N,measured_tangential_force_N,
accel_X_m_s2,accel_Y_m_s2,accel_Z_m_s2,
contact_state,surface_id,probe_id,session_id,trial_id,calibration_id
```

If the rig controls height rather than force, call the input a height command and record the resulting normal force. Do not describe it as a perfectly controlled normal-load experiment. A later forward model will need a normal contact relation or another justified way to compute the reaction force.

Save metadata separately: geometry, counterface, material specimen, mounting, trial conditions, raw paths, and QC flags. Define valid sliding intervals using calibrated motion/contact criteria before scoring model errors.

Before collection, write `configs/mechanics_protocol.yaml` with the reference speed/load, supported observation durations, input interface, specimen/session split, trial reservations, query conditions, primary metric, and exclusion rules. A concrete five-repeat starting contract is:

| Trial role | Permitted use |
| --- | --- |
| Repeat 0 at the reference speed/load | Brief support; initially the first 0.5 seconds of valid steady sliding, with nested durations if feasible |
| Repeats 0–2 at all conditions | Reserved richer calibration pool; disclosed higher-data reference only |
| Repeats 3–4 at nonreference conditions | Common query trials for every method; no fitting or test-surface calibration |

These role restrictions govern calibration and prediction for a held-out surface. Global coefficients, shared parameters, and tactile regressions may be fitted from all allowed training-surface records; in each inner validation fold, apply the same brief-support/query separation to its held-out surfaces and hide their query targets during fitting. The brief support trial is within the richer pool, but only its prescribed prefix is visible to brief methods. In the main cross-condition result, exclude the reference speed/load from queries. Evaluate all remaining valid speed/load cells with separate query trials and identical per-surface aggregation for every method. Save trial IDs and exact intervals; invalid trials follow frozen replacement/exclusion rules.

Balance collection order so reserved query repeats are not automatically later in time; repeat labels designate independent trials, not a chronological block. Distribute each role across sessions when feasible and disclose the session assignments. A same-session result and a deliberately held-out-session result answer different questions. Report extra calibration time/travel for the richer reference. If the rig cannot supply this contract, revise it before examining held-out outcomes.

**Output:** a versioned force/tactile/motion pilot dataset, mechanical episode manifest, and collection notes.

**Checkpoint:** independent trials and sessions are identifiable, and each target force has a synchronized action and motion context.

## Step 21. Fit the simplest sliding-friction model first

For confirmed one-dimensional sliding, the starter law is:

\[
F_t=-\mu_k F_n\operatorname{sign}(v).
\]

Fit the effective coefficient using only allowed support intervals. The measured normal/tangential support forces are legitimate inputs for this **force-informed** calibration.

Put the following numerical helper in `src/tactile_contact/friction.py`:

```python
import numpy as np

def fit_sliding_mu(normal_force, tangential_force, velocity,
                   min_normal=0.05, min_speed=0.001):
    """Fit a nonnegative Coulomb coefficient from confirmed sliding support.

    SI units; velocity is signed. Thresholds must be calibrated for the rig.
    The measured tangential force is the contact force on the moving body.
    """
    if (not np.isfinite(min_normal) or min_normal <= 0
            or not np.isfinite(min_speed) or min_speed < 0):
        raise ValueError("Invalid sliding thresholds")
    fn = np.asarray(normal_force, dtype=np.float64)
    ft = np.asarray(tangential_force, dtype=np.float64)
    v = np.asarray(velocity, dtype=np.float64)
    if fn.shape != ft.shape or fn.shape != v.shape or fn.ndim != 1:
        raise ValueError("Expected aligned one-dimensional arrays")
    valid = (np.isfinite(fn) & np.isfinite(ft) & np.isfinite(v)
             & (fn > min_normal) & (np.abs(v) > min_speed))
    if valid.sum() < 3:
        raise ValueError("Insufficient valid sliding samples")
    resistance = -ft[valid] * np.sign(v[valid])
    denominator = np.dot(fn[valid], fn[valid])
    numerator = np.dot(fn[valid], resistance)
    if not np.isfinite(denominator) or denominator <= 0 or not np.isfinite(numerator):
        raise ValueError("Invalid force-regression scale")
    mu = max(0.0, numerator / denominator)
    return float(mu)
```

Pass only the support interval to this function, not the full trial if that exceeds the observation budget. Validate that `min_normal` is finite and positive and `min_speed` is finite and nonnegative before applying rig-specific thresholds. Flag systematic negative resistance as a possible sign/calibration problem rather than accepting the nonnegative clamp as evidence of zero friction. Temporally correlated samples support the fit but do not provide that many independent repeats for uncertainty estimates.

Check sign convention with a known synthetic or physical direction before using this helper. If the force instrument reports the reaction on the fixture rather than the moving body, transform the sign explicitly.

Compare four methods:

1. One global coefficient fitted from training surfaces.
2. A per-surface Coulomb fit from the permitted brief support.
3. A modest speed-dependent law or learned prior using the same support budget.
4. Richer per-surface calibration using many contacts, disclosed as a higher-data reference.

An initial speed-dependent extension can use `mu(v) = max(0, mu_support + beta * log(abs(v)/v_support))` in the calibrated nonzero-speed range. Fit the shared coefficient `beta` from training surfaces. Do not assume the relation holds outside that range or near zero speed. Add load or history dependence only if the data support identifying it.

The direct support-force fit may already work well. If it wins, use it in the simulator and report the limited benefit of learning. That outcome still answers a useful research question.

**Output:** fitted contact parameters, force predictions, and same-budget mechanical baselines.

**Checkpoint:** a fitted coefficient produces forces with the correct units and direction, and no target/query interval was used to fit a test surface.

## Step 22. Test whether tactile observations add useful mechanical information

Separate two inference interfaces:

| Interface | Permitted support inputs | Claim being tested |
| --- | --- | --- |
| Force-informed | Short measured normal/tangential forces, motion, and optionally tactile signals | Efficient calibration and prediction from measured probing |
| Tactile-informed | Tactile/acceleration support and known commands/conditions; independent support-force labels hidden from inference | Whether tactile evidence can predict contact behavior without direct force calibration at deployment |

Use independent force measurements as training supervision and test ground truth in both cases. If you expose support force to the model, do not call that model tactile-only.

Start with simple regression from support features to effective friction behavior, trained on the mechanical training surfaces. With only 8–12 specimens, a large neural model is unlikely to be well justified. Compare known conditions alone, tactile features plus conditions, and the force-informed fit where applicable.

A public-data encoder trained with another probe or apparatus is an optional transfer experiment. Test it against newly fitted simple features and report the domain change. Do not assume ExSARN or the Cluster encoder transfers unchanged to a different sensor or mounting.

For the small pilot, use grouped leave-one-surface-out evaluation. For each held-out surface, choose hyperparameters using only the remaining surfaces or inner validation groups. Allow only its brief prescribed support during inference. Its query trials remain hidden until scoring.

Primary targets: measured tangential-force error in newtons and dependence on requested speed/load. Aggregate within trial, then condition, then held-out surface; bootstrap surfaces/groups rather than force samples. Keep brief support and richer calibration separate from the reserved query trials in Step 20. For a deployable prescribed-load prediction, use commanded load and commanded motion as inputs. A separate analysis using future measured query normal force can diagnose the conditional force law, but must be labeled as an oracle diagnostic. In a forward simulator, the normal force must instead come from the solver or a justified known-loading setup.

Test parameter ambiguity: refit with different support subsets and inspect whether similar support errors imply divergent held-out predictions. Large variation can indicate insufficient excitation, noise, or an overparameterized law.

**Output:** mechanical comparison tables, input-interface descriptions, and parameter-stability analysis.

**Checkpoint:** you can distinguish inference benefits from additional force information, and every held-out prediction uses an explicitly documented deployment interface.

## Step 23. Validate a simple forward motion model

First validate a very restricted physical situation: a known-mass body coasting under sliding friction on the same counterface and geometry, with no applied tangential force after release. This requires a fixture or free degree of freedom that actually permits the body to respond dynamically.

A servo-controlled scan can validate reaction forces, but matching its commanded position is not a free-motion prediction. Keep this distinction explicit.

The following numerical helper is an exact within-step update for constant Coulomb deceleration in an **unforced coasting** experiment. It is not a general sticking/sliding engine:

```python
import numpy as np

def simulate_coast(v0, mass, mu, normal_load, dt=0.001, steps=1000):
    """Return columns time, position, velocity for unforced planar coasting.

    SI units. Constant known normal load; no tangential applied force.
    Velocity is clamped at the stopping event and remains zero thereafter.
    """
    values = np.array([v0, mass, mu, normal_load, dt], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Parameters must be finite")
    if mass <= 0 or mu < 0 or normal_load < 0 or dt <= 0:
        raise ValueError("Invalid physical parameter")
    if not isinstance(steps, (int, np.integer)) or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    out = np.zeros((steps + 1, 3), dtype=np.float64)
    v = float(v0)
    x = 0.0
    deceleration = mu * normal_load / mass
    out[0] = [0.0, x, v]
    for i in range(steps):
        if deceleration > 0 and v != 0:
            direction = np.sign(v)
            moving_time = min(dt, abs(v) / deceleration)
            x += v * moving_time - 0.5 * direction * deceleration * moving_time**2
            v = direction * max(0.0, abs(v) - deceleration * dt)
        else:
            x += v * dt
        out[i + 1] = [(i + 1) * dt, x, v]
    return out
```

Verify it before using real parameters. For positive initial speed and nonzero friction:

\[
t_{\mathrm{stop}}=\frac{m v_0}{\mu N},\qquad
d_{\mathrm{stop}}=\frac{m v_0^2}{2\mu N}.
\]

The implementation should match this result, never reverse velocity because of friction, and preserve constant velocity when `mu=0`. Check both signs of initial velocity. These numerical checks validate the implementation, not its realism on textured materials.

For real validation, keep contact geometry and probe/surface pairing consistent with the fitted law, know the moving mass and normal loading, and characterize additional guide drag. Use only initial state and known loading in prediction. Future measured velocity or force cannot be supplied to rescue the rollout.

Use initial speeds and loads inside the calibrated range. The helper's analytical examples are numerical checks, not proposed hardware settings. Inspect the low-speed stopping regime separately; a law fitted during steady sliding may miss real behavior near a stop.

Compare global/default friction, brief-contact calibration, and the richer calibration reference on held-out surfaces. Score velocity error, position error, and stopping distance when the experiment supports that metric. Include measured uncertainty in initial speed, mass, and loading when interpreting errors.

**Output:** numerical simulator verification and, when hardware permits, real held-out motion comparisons.

**Checkpoint:** the contact parameters influence predicted motion and are evaluated against measurements the simulator did not consume as future inputs.

## Step 24. Integrate the validated contact model into an existing engine

After a restricted force/motion validation, use an existing physics engine for known-geometry bodies. Start with native contact parameters rather than combining a custom learned force with an already active friction model.

For a MuJoCo experiment, an explicit contact pair makes the coefficient assignment clear. Example configuration fragment, assuming these geoms exist:

```xml
<contact>
  <pair name="probe_surface" geom1="probe_geom" geom2="surface_geom"
        condim="3" friction="0.5 0.5 0 0 0"/>
</contact>
```

Illustrative coefficient assignment after loading a model:

```python
import mujoco

pair_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_PAIR, "probe_surface")
if pair_id < 0:
    raise ValueError("Expected contact pair is missing")
model.pair_friction[pair_id, :2] = mu_hat
```

Validate signs, normal forces, timestep sensitivity, and energy dissipation with a simple slider before adding a robot. Native parameter semantics and the solver's contact approximation must be understood; an effective fit is specific to the experiment and engine setup.

The coefficient assignment above implements a constant Coulomb parameter. It does not implement the speed-dependent extension from Step 21. Start with the constant law. If a variable law has verified benefits, integrating it requires a separately validated implementation that replaces the relevant native resistance rather than adding a second friction force.

Attach a separate tactile observation module that predicts spectral features from permitted simulated contact conditions. The public model is trained on steady-window spectra and two nominal loads. Its first integration should therefore use compatible steady-contact conditions and feature observations. Do not claim instantaneous transient waveforms or arbitrary continuous-load rendering from that benchmark.

If you later generate waveforms, study phase reconstruction or a generative renderer such as HaptoFlow only after validating spectral/amplitude prediction. Keep renderer quality and mechanical fidelity as separate measurements.

**Output:** an engine scene, parameter-inference interface, contact-force checks, and a clearly scoped tactile observation interface.

**Checkpoint:** changing the inferred friction parameter changes mechanical response, while tactile output is generated by a separately evaluated observation model.

## Step 25. Test usefulness for planning or robot learning

Choose one task after validating force and motion: for example, move a known object to a target while respecting a force limit. Begin with a controller or planner before a large reinforcement-learning experiment.

Compare fixed global/default contact parameters, brief-contact-calibrated parameters, and a learned contact model only if it has demonstrated predictive value.

Hold controller/policy architecture, training budget, action limits, real-data budget, task distribution, and test surfaces constant. Measure task success, position error, force-limit violations, probing time, and adaptation cost.

If testing tactile observation quality, vary that factor separately from dynamics. Otherwise an improved result cannot establish whether it came from better forces, richer observations, or additional training data.

A planning/control result establishes decision-making usefulness. Claims about robot learning or sim-to-real transfer require the corresponding matched training and real evaluation. You can keep these as follow-up milestones rather than delaying the first completed study indefinitely.

**Output:** one matched downstream task evaluation, or an explicit future-work specification.

**Checkpoint:** an improvement has a traceable cause and was measured on held-out surfaces/tasks appropriate to the claim.

## Step 26. Package the research so another person can assess it

Create a top-level `README.md` explaining the question, supported claims, dataset revision, environment, data preparation, experiment configurations, figure regeneration, and limitations. Include the exact commands for the scripts you implemented, not hypothetical commands for missing files.

The research record should contain:

- Protocol and related-work comparison.
- Data/QC manifests, specimen groups, split files, and window/episode definitions.
- Training-only fitted preprocessing and baseline parameters.
- Model checkpoints and configuration hashes.
- Per-query and per-surface numerical results.
- Figures generated from those results.
- Report and appendix.
- A contribution statement identifying your work, guidance, reused code, and verified results.

Keep a weekly log: question, attempted experiment, reason, outcome, interpretation, and next decision. Record failed approaches when they clarify a methodological choice. Distinguish exploratory tuning from locked evaluation.

For a PhD application, describe completed evidence accurately. Example structure:

> I investigated whether brief sliding contacts support prediction on held-out surfaces. I designed matched-budget probe comparisons, implemented retrieval and physical-rescaling baselines, and evaluated response prediction across interaction conditions. The study found [verified result], which motivated [specific next experiment].

Fill brackets only with actual results. Label an unpublished report as a technical report or preprint, a submitted paper as submitted, and acceptance only after acceptance. A short conversation with a researcher does not establish supervision or a recommendation commitment.

The credible evidence is your scientific question, experimental ownership, validation, and interpretation. Publication suitability depends on novelty and results; admissions outcomes also depend on the rest of the application.

**Output:** a complete, reviewable research package and an accurate completed-work description.

**Checkpoint:** someone can reproduce the principal tables and understand your contribution without reading this conversation.

## Recommended execution order and time budget

| Period | Focus | Milestone |
| --- | --- | --- |
| First 2–3 days | Steps 1–5 | Protocol, closest-work matrix, pilot data, and manifest |
| Rest of week 1 | Steps 6–9 | Synchronized plots, QC/window decisions, spectral features |
| Week 2 | Steps 10–12 | Locked splits/episodes and functioning baselines |
| Week 3 | Steps 13–15 | Small model, engineering checks, validation decisions |
| Week 4 | Steps 15–16 | Locked evaluation and paired numerical comparisons |
| Week 5 | Steps 17 and 26 | Finished public-data report and reproducible record |
| Weeks 6–8 or later, depending on rig access | Steps 18–22 | Calibrated sliding-force pilot; revise timing to match actual collection capacity |
| Later, with dynamically responsive hardware | Steps 23–24 | Restricted real motion validation and engine integration |
| After model validation | Step 25 | Matched downstream task |

These are planning estimates, not promises. Seek rig access during the public study. If hardware takes longer, complete and report the public-data milestone rather than keeping all work indefinitely in progress.

## Stage A experiment matrix and conditional extensions

| Experiment | Required methods | Required outcome |
| --- | --- | --- |
| New surfaces, familiar conditions | Conditions-only, copy, retrieval, fixed-feature regression, encoder, direction-agnostic rescaling; same-direction diagnostic for all | Per-surface spectral/amplitude errors |
| Probe duration | Same methods at 0.25/0.5/1 s on matched cohort | Error versus observed time |
| One versus two probes at equal total time | Single 1 s versus two 0.5 s; single 0.5 s versus two 0.25 s | Benefit of probe diversity beyond additional observation time |
| Second-probe choice | Repetition/speed/load/direction, fixed 0.5-second contact duration for the main contrast; other durations secondary | Same-budget comparison; count time and distance |
| Wrong-support control | Proposed predictor with correct and substituted support | Evidence of surface-specific conditioning |
| Globally omitted speeds | Refit relevant methods with 20/40/60 only | 30/50 predictions without hidden-label retrieval |
| Mechanical pilot, when feasible | Global coefficient, brief-force fit, modest extension, richer calibration | Held-out force error and parameter stability |
| Restricted real dynamics, when feasible | Global, brief-contact, richer calibration | Motion error without future-state inputs |

Run the `single`, 0.5-second development slice end to end on training/validation surfaces before expanding this matrix. Category exclusion and globally omitted directions are optional exploratory stress tests. Adaptive next-probe selection, waveform synthesis, compliance, and sensor transfer need separately scoped experiments after the planned study is complete.

## Troubleshooting guide

| Symptom | Check first | Avoid concluding prematurely |
| --- | --- | --- |
| All test errors are exceptionally small | Material splits, same-record overlap, query labels, retrieval omitted-speed access | Universal material representation |
| All amplitude errors are large | g-to-SI conversion, per-record normalization, PSD density integration, log inversion | Insufficient network size |
| Frequency shifts look wrong | Sampling/time base, speed units, interpolation scaling factor | Material physics is unpredictable |
| More contact always helps enormously | Hidden query-condition observations, unmatched time/distance, cohort changes | A special information-theoretic benefit |
| Wrong surface performs equally well | Support ignored, query-condition dominance, machine signal | Surface identification |
| Force model fits support but fails elsewhere | Confirmed sliding, load control, calibration drift, parameter ambiguity | Intrinsic friction has been recovered |
| Simulation matches a scan exactly | Whether measured future motion was replayed | Forward dynamics accuracy |
| Controller improves with new model | Data/training budget and observation/dynamics changes | Sim-to-real or robot-learning improvement |

## References and official implementation resources

- **[R1] Heravi et al. Learning an Action-Conditional Model for Haptic Texture Generation. ICRA 2020.** [Paper](https://arxiv.org/abs/1909.13025).
- **[R2] Heravi et al. Development and Evaluation of a Learning-based Model for Real-time Haptic Texture Rendering. IEEE Transactions on Haptics, 2024.** [Paper](https://arxiv.org/abs/2212.13332).
- **[R3] Eguchi et al. Cluster Haptic Texture Dataset: Haptic Texture Dataset with Varied Velocity–Direction Sliding Contacts. Scientific Data 13, 756 (2026).** [Published article](https://www.nature.com/articles/s41597-026-06760-z), [author manuscript](https://arxiv.org/html/2407.16206v4), [data mirror and schema](https://huggingface.co/datasets/tamago117/cluster-haptic-texture-dataset), [author code](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset), [collection/file documentation](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset/blob/main/documents/dataset_details.md).
- **[R4] Gao et al. On Explainability and Sensor-Adaptability of a Robot Tactile Texture Representation Using a Two-Stage Recurrent Networks. IROS 2021 — ExSARN.** [Final publication](https://ieeexplore.ieee.org/document/9636380), [author code/data](https://github.com/dexrob/ExSARN).
- **[R5] Eguchi et al. HaptoFlow: High-Fidelity Real-Time Vibrotactile Generation via Flow Matching for Virtual Reality. 2026 arXiv manuscript; arXiv reports acceptance to IEEE ISMAR 2026.** [Paper](https://arxiv.org/abs/2608.01974).
- **[R6] Si et al. DiffTactile: A Physics-based Differentiable Tactile Simulator for Contact-rich Robotic Manipulation. ICLR 2024.** [Paper](https://arxiv.org/abs/2403.08716), [project](https://difftactile.github.io/), [code](https://github.com/Genesis-Embodied-AI/DiffTactile).
- **[R7] TacTID: High-Performance Visuo-Tactile Sensor-Based Terrain Identification for Legged Robots. IEEE Sensors Journal, 2024.** [Author-hosted paper](https://charon-bo.github.io/assets/PDF/TacTID.pdf).
- **[R8] Gao et al. Tactile DreamFusion: Exploiting Tactile Sensing for 3D Generation. NeurIPS 2024.** [Paper](https://arxiv.org/abs/2412.06785). Useful for a later 3D texture-generation direction, rather than a dependency of this first benchmark.
- **Hugging Face Hub download API.** [Official download guide](https://huggingface.co/docs/huggingface_hub/guides/download), [HfApi reference](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api).
- **SciPy Welch estimation.** [Official documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html).
- **PyTorch installation.** [Official selector](https://pytorch.org/get-started/locally/).
- **MuJoCo contact model.** [Official computation documentation](https://mujoco.readthedocs.io/en/stable/computation/index.html), [XML contact-pair reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html#contact-pair).
- **CMU research-statement guidance.** [Jonathan Aldrich's faculty guidance](https://www.cs.cmu.edu/~aldrich/essay-advice.html).

## Refinement and validation record

This revision preserves the plan's stages and research question while making the primary analysis, development milestone, baseline contracts, support-prefix budgets, and mechanical trial roles explicit. It also distinguishes statistical inconclusiveness from equivalence and orthogonal-probe benefit from intrinsic anisotropy. Source checks on 8 October 2026 confirmed the cited Cluster acquisition/schema facts, Heravi's retrieval precedent, and HaptoFlow's reported status; sensor acquisition timing and access to mechanical recordings remain unresolved.

All 15 Python blocks were syntax-checked and the contact-pair XML fragment was parsed. Synthetic checks passed for filename/condition validation; spectral peaks, amplitude scaling, offset removal, all three support durations, and modeled-band RMS reconstruction; grouped bootstrap determinism and missing/mixed-ID rejection; sliding-friction fitting for both velocity signs and invalid thresholds; and coasting motion with both velocity signs, within-step stopping, and zero friction. The 76-condition common query grid and all 26 step headings were checked.

The PyTorch model was executed for forward/backward sanity checks, output dimensions, finite masked-padding invariance, support-order invariance, and invalid-input guards. Runtime: Python 3.12.6, NumPy 1.26.4, SciPy 1.15.1, PyTorch 2.6.0+cu118; model checks ran on CPU. This is example verification, not a trained-model evaluation.

These checks establish example behavior, not research results. Dataset download, real-data windowing, scientific model training/evaluation, physical force calibration, and full MuJoCo integration require the experiments described above. Script names remain implementation contracts, not a delivered executable research repository.
