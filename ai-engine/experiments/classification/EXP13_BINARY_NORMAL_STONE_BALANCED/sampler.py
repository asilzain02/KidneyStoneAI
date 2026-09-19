"""
sampler.py — EXP13 Balanced Sampler

Creates a WeightedRandomSampler that gives equal expected frequency
to Normal and Stone samples in the training loader.

ONLY applied to the training set.
Validation, test, and external datasets are never sampled — they
use the natural distribution.

No image files are copied or duplicated.
"""

from __future__ import annotations

from typing import List

import torch
from torch.utils.data import WeightedRandomSampler


def make_balanced_sampler(
    labels: List[int],
    num_classes: int = 2,
    replacement: bool = True,
) -> WeightedRandomSampler:
    """
    Build a WeightedRandomSampler such that each class has equal expected
    frequency per epoch.

    Parameters
    ----------
    labels      : list of integer labels for every training sample
    num_classes : number of classes (2 for EXP13)
    replacement : sample with replacement (True = allows oversampling)

    Returns
    -------
    WeightedRandomSampler
    """
    label_tensor = torch.tensor(labels, dtype=torch.long)
    class_counts = torch.zeros(num_classes)
    for lbl in label_tensor:
        class_counts[lbl] += 1

    # Weight per class = 1 / count
    # Every class gets the same expected draw frequency
    class_weights = 1.0 / class_counts.clamp(min=1)

    # Per-sample weight
    sample_weights = class_weights[label_tensor]

    # Total draws = same as original dataset length
    # (so epochs are roughly the same length regardless of balance)
    num_samples = len(labels)

    sampler = WeightedRandomSampler(
        weights=sample_weights.tolist(),
        num_samples=num_samples,
        replacement=replacement,
    )
    return sampler


def summarise_balance(labels: List[int], class_names: List[str]) -> None:
    """Print a balance summary before training starts."""
    counts = {}
    for lbl in labels:
        counts[lbl] = counts.get(lbl, 0) + 1
    total = len(labels)
    print("\n  Sampler balance summary (raw training counts):")
    for idx, name in enumerate(class_names):
        n = counts.get(idx, 0)
        pct = n / total * 100 if total > 0 else 0
        print(f"    {name:10s}: {n:5d}  ({pct:.1f}%)")
    print(f"  {'Total':10s}: {total:5d}")
    print(f"\n  WeightedRandomSampler will equalise draw frequency.")
    print(f"  Draws per epoch: {total} (same as raw dataset size)")
