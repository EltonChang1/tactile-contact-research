"""Numerical starter code from the user-provided refined implementation guide."""


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
