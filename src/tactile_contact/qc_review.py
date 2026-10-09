"""Diagnostic geometry/loading helpers; these do not change pipeline eligibility."""
import numpy as np


def local_velocity(values, times, samples=21):
    values, times = np.asarray(values, float), np.asarray(times, float)
    if values.shape != (len(times), 2) or len(times) < 3 or samples < 3:
        raise ValueError("Need at least three XY samples")
    if not np.isfinite(values).all() or not np.isfinite(times).all() or (np.diff(times) <= 0).any():
        raise ValueError("Need finite increasing position times")
    window = min(samples, len(times))
    half = window//2
    velocity = np.empty_like(values)
    for i in range(len(times)):
        start = max(0, min(i-half, len(times)-window))
        selected = slice(start, start+window)
        velocity[i] = np.polynomial.polynomial.polyfit(times[selected]-times[i], values[selected], 2)[1]
    return velocity


def wrap_degrees(angle):
    return (np.asarray(angle)+180) % 360-180


def fit_heading_frame(observed_degrees, nominal_degrees):
    """One global offset/sign fit, equal weight per record; no per-record correction."""
    observed, nominal = np.asarray(observed_degrees), np.asarray(nominal_degrees)
    if len(observed) == 0 or len(observed) != len(nominal) or not np.isfinite(observed).all():
        raise ValueError("Need finite paired headings")
    candidates = []
    for sign in [-1, 1]:
        radians = np.deg2rad(observed-sign*nominal)
        offset = float(np.rad2deg(np.arctan2(np.sin(radians).mean(), np.cos(radians).mean())))
        error = wrap_degrees(observed-(offset+sign*nominal))
        candidates.append(dict(sign=sign, offset_deg=offset, mean_absolute_residual_deg=float(np.abs(error).mean())))
    return min(candidates, key=lambda row: row["mean_absolute_residual_deg"]), candidates


def interval_samples(times, values, start, end):
    """Include interpolated exact endpoints, without extrapolation."""
    times, values = np.asarray(times), np.asarray(values)
    if not (times[0] <= start < end <= times[-1]):
        raise ValueError("Interval outside logged channel")
    inside = times[(times > start) & (times < end)]
    grid = np.r_[start, inside, end]
    if values.ndim == 1:
        return grid, np.interp(grid, times, values)
    return grid, np.column_stack([np.interp(grid, times, values[:, j]) for j in range(values.shape[1])])


def support_diagnostics(frames, times, start, duration=.5, samples=21):
    end = start+duration
    position = frames["position"][["X", "Y"]].to_numpy(float)
    velocity = local_velocity(position, times["position"], samples)
    pt, pv = interval_samples(times["position"], velocity, start, end)
    _, xy = interval_samples(times["position"], position, start, end)
    mean_velocity = np.trapz(pv, pt, axis=0)/duration
    heading = np.rad2deg(np.arctan2(mean_velocity[1], mean_velocity[0]))
    instantaneous = np.rad2deg(np.arctan2(pv[:, 1], pv[:, 0]))
    ft, force = interval_samples(times["force"], frames["force"].force.to_numpy(float), start, end)
    mean = np.trapz(force, ft)/duration
    std = np.sqrt(np.trapz((force-mean)**2, ft)/duration)
    # Time-weighted linear trend; repeated transmitted rows are not independent observations.
    centered = ft-(start+end)/2
    slope = np.trapz(centered*(force-mean), ft)/np.trapz(centered**2, ft)
    return dict(observed_heading_deg=float(heading), heading_within_window_p95_deg=float(np.percentile(np.abs(wrap_degrees(instantaneous-heading)), 95)),
        logged_position_travel_mm=float(np.trapz(np.linalg.norm(pv, axis=1), pt)),
        endpoint_displacement_mm=float(np.linalg.norm(xy[-1]-xy[0])),
        logged_speed_mean_mm_s=float(np.trapz(np.linalg.norm(pv, axis=1), pt)/duration),
        force_time_weighted_mean_N=float(mean), force_time_weighted_std_N=float(std),
        force_trend_N_s=float(slope), force_trend_change_N=float(slope*duration),
        force_min_N=float(force.min()), force_max_N=float(force.max()),
        force_logged_rows=int(((times["force"] >= start) & (times["force"] < end)).sum()))
