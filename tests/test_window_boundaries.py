import numpy as np
import pandas as pd
import pytest

from tactile_contact.signal import spectral_features
from tactile_contact.windows import prepare_acceleration_window, extract_windows, PROCESSING_BOUNDARY


def jittered_record():
    rng = np.random.default_rng(29)
    t = np.r_[0., np.cumsum(rng.uniform(1/9500, 1/8000, 18000))]
    values = .02*np.sin(2*np.pi*173*t)[:, None]*np.array([[1., .7, .3]])
    return pd.DataFrame(values, columns=["X", "Y", "Z"]), t


@pytest.mark.parametrize("duration", [.25, .5, 1.])
def test_outside_raw_samples_cannot_change_processed_window_or_features(duration):
    frame, t = jittered_record()
    start = .301234567
    original, provenance = prepare_acceleration_window(frame, t, start, duration, 6000)
    allowed = (t >= start) & (t < start+duration)
    for outside in [t < start, t >= start+duration, ~allowed]:
        changed = frame.copy()
        changed.loc[outside, ["X", "Y", "Z"]] = np.arange(outside.sum())[:, None]*np.array([[1e5, -3e5, 7e5]])
        processed, changed_provenance = prepare_acceleration_window(changed, t, start, duration, 6000)
        np.testing.assert_array_equal(processed, original)
        np.testing.assert_array_equal(spectral_features(processed)["log_band_power"],
                                      spectral_features(original)["log_band_power"])
        assert changed_provenance == provenance
    assert original.shape == (round(duration*6000), 3)
    assert provenance["processing_boundary"] == PROCESSING_BOUNDARY
    assert provenance["raw_samples"] == allowed.sum()
    assert provenance["dependency_raw_start_index"] == np.flatnonzero(allowed)[0]
    assert provenance["dependency_raw_end_index_exclusive"] == np.flatnonzero(allowed)[-1]+1
    assert provenance["observed_context_before_s"] == provenance["observed_context_after_s"] == 0
    # Ensure the invariance result does not come from discarding allowed signals.
    changed = frame.copy()
    changed.iloc[np.flatnonzero(allowed)[len(original)//2], 0] += 100
    processed, _ = prepare_acceleration_window(changed, t, start, duration, 6000)
    assert not np.allclose(spectral_features(processed)["log_band_power"],
                           spectral_features(original)["log_band_power"])


def test_raw_dependencies_nest_but_local_filter_edges_need_not_match():
    frame, t = jittered_record()
    short, a = prepare_acceleration_window(frame, t, .3, .25, 6000)
    long, b = prepare_acceleration_window(frame, t, .3, 1., 6000)
    assert a["raw_start_index"] == b["raw_start_index"]
    assert a["raw_end_index_exclusive"] < b["raw_end_index_exclusive"]
    assert not np.array_equal(short, long[:len(short)])


@pytest.mark.parametrize("start,duration", [(-.1,.25), (1.9,.5), (.3,0.), (.3,np.nan)])
def test_invalid_observation_intervals_fail(start, duration):
    frame, t = jittered_record()
    with pytest.raises(ValueError):
        prepare_acceleration_window(frame, t, start, duration, 6000)


def test_production_extractor_crops_before_interpolation_and_filtering(prepared, tmp_path, monkeypatch):
    root, cfg, *_ = prepared
    from tactile_contact.audit import load_record
    manifest = pd.read_csv(root/"data/manifests/recordings.csv")
    manifest = manifest[(manifest.surface_id == 0) & (manifest.speed_mm_s == 40)
                        & (manifest.direction_deg == 0) & (manifest.nominal_force_N == .5)
                        & (manifest.repeat_id == 0)]
    recording = manifest.iloc[0].recording_id
    frames, times, origin = load_record(root/"data/raw/synthetic", recording)
    original_frame = frames["accel"].copy()
    monkeypatch.setattr("tactile_contact.windows.load_record", lambda *_: (frames, times, origin))
    def extract(name):
        destination = tmp_path/name
        (destination/"data/manifests").mkdir(parents=True)
        return destination, extract_windows(destination, cfg, manifest)
    before_root, before = extract("before")
    for i, window in enumerate(before.itertuples()):
        frames["accel"] = original_frame.copy()
        outside = (times["accel"] < window.start_s) | (times["accel"] >= window.end_s)
        frames["accel"].loc[outside, ["X", "Y", "Z"]] = 1e6
        after_root, after = extract(f"perturbed_{i}")
        current = after.set_index("window_id").loc[window.window_id]
        with np.load(before_root/window.feature_path) as a, np.load(after_root/current.feature_path) as b:
            for key in ["psd", "band_power", "log_band_power"]:
                np.testing.assert_array_equal(a[key], b[key])
        assert current.raw_start_index == current.dependency_raw_start_index
        assert current.raw_end_index_exclusive == current.dependency_raw_end_index_exclusive
