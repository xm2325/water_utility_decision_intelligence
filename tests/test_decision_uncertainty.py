import numpy as np
import pandas as pd
import pytest

from yw_decisioning.decision_uncertainty import block_bootstrap_policy_capture, moving_block_sample_indices


def _daily():
    rows = []
    dates = pd.date_range("2026-01-01", periods=21, freq="D")
    for i, date in enumerate(dates):
        total = float(10 + i % 4)
        for policy, fraction in [("capacity_constrained", 0.8), ("highest_flow", 0.4), ("random", 0.1)]:
            rows.append({"DATE": date, "policy": policy, "capacity": 20, "total_signal": total, "captured_signal": total * fraction})
    return pd.DataFrame(rows)


def test_moving_block_indices_preserve_contiguous_runs():
    idx = moving_block_sample_indices(20, 4, np.random.default_rng(1))
    for start in range(0, 20, 4):
        block = idx[start:start+4]
        assert np.all(np.diff(block) == 1)


def test_bootstrap_is_deterministic_for_fixed_seed():
    a, ac = block_bootstrap_policy_capture(_daily(), n_bootstrap=50, seed=9)
    b, bc = block_bootstrap_policy_capture(_daily(), n_bootstrap=50, seed=9)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(ac, bc)


def test_bootstrap_policy_difference_is_positive_for_constructed_data():
    _, c = block_bootstrap_policy_capture(_daily(), n_bootstrap=50, seed=9)
    assert (c["difference_ci_lower_pp"] > 0).all()
    assert c["bootstrap_share_difference_positive"].eq(1.0).all()


def test_bootstrap_rejects_too_short_history():
    d = _daily()[lambda x: x["DATE"] < pd.Timestamp("2026-01-05")]
    with pytest.raises(ValueError, match="not enough dates"):
        block_bootstrap_policy_capture(d, block_length=7, n_bootstrap=20)


def test_point_estimate_is_invariant_to_block_length():
    s3, _ = block_bootstrap_policy_capture(_daily(), block_length=3, n_bootstrap=30, seed=2)
    s7, _ = block_bootstrap_policy_capture(_daily(), block_length=7, n_bootstrap=30, seed=2)
    a = s3.set_index("policy")["point_signal_capture"].sort_index()
    b = s7.set_index("policy")["point_signal_capture"].sort_index()
    pd.testing.assert_series_equal(a, b)
