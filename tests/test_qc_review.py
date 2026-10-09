import numpy as np
import pandas as pd
import pytest

from tactile_contact.audit import motion_speed
from tactile_contact.qc_review import local_velocity, fit_heading_frame, interval_samples, support_diagnostics, wrap_degrees


def test_velocity_matches_existing_speed_on_jittery_quadratic_path():
    t = np.cumsum(np.linspace(.009, .011, 80))
    xy = np.column_stack([2*t**2+3*t, -t**2+4*t])
    velocity = local_velocity(xy, t, 21)
    np.testing.assert_allclose(velocity, np.column_stack([4*t+3, -2*t+4]), atol=1e-10)
    np.testing.assert_array_equal(np.linalg.norm(velocity, axis=1), motion_speed(pd.DataFrame(xy, columns=["X", "Y"]), t, 21))


def test_global_heading_frame_infers_rotation_and_sign():
    nominal = np.tile([0, 45, 90], 3)
    observed = wrap_degrees(90-nominal)
    best, candidates = fit_heading_frame(observed, nominal)
    assert best["sign"] == -1
    assert best["offset_deg"] == pytest.approx(90)
    assert best["mean_absolute_residual_deg"] < 1e-10
    assert len(candidates) == 2


def test_exact_endpoints_and_no_extrapolation():
    t, x = interval_samples(np.array([0., 1., 2.]), np.array([0., 2., 4.]), .25, 1.75)
    np.testing.assert_array_equal(t, [.25, 1., 1.75])
    np.testing.assert_array_equal(x, [.5, 2., 3.5])
    with pytest.raises(ValueError, match="outside"):
        interval_samples(np.array([0., 1.]), np.array([0., 1.]), -.1, .8)


def test_travel_heading_and_time_weighted_force_on_known_motion():
    t = np.linspace(0, 1, 101)
    frames = {"position": pd.DataFrame({"X": t*30, "Y": t*40}), "force": pd.DataFrame({"force": .5+.2*t})}
    output = support_diagnostics(frames, {"position": t, "force": t}, .2, .5)
    assert output["observed_heading_deg"] == pytest.approx(np.rad2deg(np.arctan2(40, 30)))
    assert output["logged_position_travel_mm"] == pytest.approx(25)
    assert output["endpoint_displacement_mm"] == pytest.approx(25)
    assert output["force_time_weighted_mean_N"] == pytest.approx(.59)
    assert output["force_trend_change_N"] == pytest.approx(.1)
