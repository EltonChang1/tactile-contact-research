"""Numerical starter code from the user-provided refined implementation guide."""


import numpy as np
from scipy.signal import welch


def integrate_bands(frequency_hz, psd, edges=None):
    """Shared bin-center convention for targets and warped full spectra."""
    frequency_hz = np.asarray(frequency_hz)
    psd = np.asarray(psd)
    edges = np.linspace(24.,1000.,33) if edges is None else np.asarray(edges)
    if psd.shape != (len(frequency_hz),3) or not np.isfinite(psd).all() or (psd < 0).any():
        raise ValueError("Expected a finite nonnegative three-axis PSD")
    delta = np.diff(frequency_hz)
    if not len(delta) or delta[0] <= 0 or not np.allclose(delta,delta[0]):
        raise ValueError("Expected a uniform increasing frequency grid")
    bands, counts = [],[]
    for j,(lo,hi) in enumerate(zip(edges[:-1],edges[1:])):
        selected = (frequency_hz >= lo) & ((frequency_hz <= hi) if j == len(edges)-2 else (frequency_hz < hi))
        if not selected.any():
            raise ValueError("Empty frequency band; revise the spectral settings")
        bands.append(psd[selected].sum(axis=0)*delta[0]); counts.append(int(selected.sum()))
    return np.stack(bands),np.array(counts)

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
    band_power,bin_counts = integrate_bands(frequency_hz,psd,edges)
    log_band_power = np.log10(band_power + floor)
    rms_by_axis = np.sqrt(band_power.sum(axis=0))
    return {
        "frequency_hz": frequency_hz,
        "psd": psd,
        "band_edges_hz": edges,
        "band_bin_counts": bin_counts,
        "band_power": band_power,
        "log_band_power": log_band_power,
        "rms_by_axis": rms_by_axis,
        "floor": float(floor),
    }

import numpy as np

def condition_vector(speed_mm_s, direction_deg, nominal_force_N):
    theta = np.deg2rad(direction_deg)
    return np.array([
        speed_mm_s / 40.0,
        np.cos(theta),
        np.sin(theta),
        nominal_force_N / 0.5,
    ], dtype=np.float32)

import numpy as np

def rms_from_log_power(log_power, floor=1e-10):
    log_power = np.asarray(log_power, dtype=np.float64).reshape(-1, 32, 3)
    linear_power = np.maximum(np.power(10.0, log_power) - floor, 0.0)
    rms_axes = np.sqrt(linear_power.sum(axis=1))
    rms_total = np.sqrt(linear_power.sum(axis=(1, 2)))
    return rms_axes, rms_total
