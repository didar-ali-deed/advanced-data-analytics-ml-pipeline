"""Resampling and multiplicity tools with explicit units of analysis."""

import numpy as np


def holm_adjust(pvalues) -> list[float]:
    """Control family-wise error for a fixed family of hypotheses."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty(len(p))
    adjusted[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return adjusted.tolist()


def bootstrap_difference(a, b, repetitions: int, seed: int) -> list[float]:
    """Independent customer-level bootstrap CI for mean(a)-mean(b)."""
    rng = np.random.default_rng(seed)
    differences = [
        rng.choice(a, len(a), replace=True).mean() - rng.choice(b, len(b), replace=True).mean()
        for _ in range(repetitions)
    ]
    return np.quantile(differences, [0.025, 0.975]).tolist()


def block_bootstrap_mean(values, repetitions: int, block: int, seed: int) -> list[float]:
    """Moving-block mean CI preserving local serial dependence, conditional on this era."""
    values = np.asarray(values)
    if len(values) < block:
        raise ValueError("History is shorter than the requested bootstrap block")
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(repetitions):
        starts = rng.integers(0, len(values) - block + 1, size=int(np.ceil(len(values) / block)))
        sample = np.concatenate([values[start : start + block] for start in starts])[: len(values)]
        means.append(sample.mean())
    return np.quantile(means, [0.025, 0.975]).tolist()
