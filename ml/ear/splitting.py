"""Stratified dataset splitting and integrity checks for canine ear disease images.

Provides reproducible class-stratified train/validation/test partitioning and
detects duplicate/near-duplicate image files prior to model optimization.

METHODOLOGICAL NOTE & LIMITATION:
The canine ear disease image dataset is assumed to lack patient/dog-level identifiers and utilizes
synthetic fallback IDs (`img_fallback_<class>_<idx>`). Therefore, this splitting
strategy operates at the image level rather than the dog subject level. It guarantees
class balance across splits, but cannot prevent subject leakage if multiple photos of
the same animal exist in the source dataset. Test data is strictly sequestered and
must never be utilized during training or hyperparameter selection.
"""

import hashlib
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union


def detect_duplicate_images(
    data_dir: Union[str, Path],
    records: Sequence[dict],
) -> Dict[str, List[str]]:
    """Scan records and detect identical images using SHA-256 byte hashing.

    Args:
        data_dir: Root directory where image files are stored.
        records: List of manifest record dictionaries containing 'image_path'.

    Returns:
        Dict mapping SHA-256 hex digests to lists of relative paths for duplicates.
        Returns an empty dict if all images have unique byte contents.
    """
    root = Path(data_dir)
    hash_to_paths: Dict[str, List[str]] = defaultdict(list)

    for record in records:
        rel_path = record["image_path"]
        full_path = root / rel_path
        if not full_path.is_file():
            continue

        hasher = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        digest = hasher.hexdigest()
        hash_to_paths[digest].append(rel_path)

    # Filter down to only digests that have more than 1 image path
    duplicates = {d: paths for d, paths in hash_to_paths.items() if len(paths) > 1}
    return duplicates


def stratified_train_val_test_split(
    records: Sequence[dict],
    label_key: str = "label",
    ratios: Tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Split records into train, validation, and test subsets with class stratification.

    Args:
        records: List of manifest record dictionaries.
        label_key: Dictionary key identifying the class label.
        ratios: Tuple of (train_ratio, val_ratio, test_ratio). Must sum to 1.0.
        seed: Random seed for deterministic reproducibility.

    Returns:
        Tuple of (train_records, val_records, test_records).
    """
    if abs(sum(ratios) - 1.0) > 1e-6:
        raise ValueError(f"Split ratios must sum to 1.0, got {ratios} (sum={sum(ratios)})")

    train_ratio, val_ratio, _test_ratio = ratios

    # Group records by class label
    class_groups: Dict[str, List[dict]] = defaultdict(list)
    for r in records:
        class_groups[r[label_key]].append(r)

    rng = random.Random(seed)

    train_records: List[dict] = []
    val_records: List[dict] = []
    test_records: List[dict] = []

    # Deterministically shuffle and partition each class independently
    for label, group in sorted(class_groups.items()):
        # Copy and sort first to guarantee identical initial state across platforms
        sorted_group = sorted(group, key=lambda x: x.get("image_path", ""))
        shuffled = sorted_group.copy()
        rng.shuffle(shuffled)

        n_total = len(shuffled)
        n_train = int(round(n_total * train_ratio))
        n_val = int(round(n_total * val_ratio))

        # Ensure every class with sufficient samples has representation
        if n_train == 0 and n_total > 0:
            n_train = 1
        if n_val == 0 and (n_total - n_train) >= 2:
            n_val = 1

        train_chunk = shuffled[:n_train]
        val_chunk = shuffled[n_train : n_train + n_val]
        test_chunk = shuffled[n_train + n_val :]

        train_records.extend(train_chunk)
        val_records.extend(val_chunk)
        test_records.extend(test_chunk)

    # Verification: Ensure zero intersection among splits
    train_paths = {r["image_path"] for r in train_records}
    val_paths = {r["image_path"] for r in val_records}
    test_paths = {r["image_path"] for r in test_records}

    assert not (train_paths & val_paths), "Data leakage: overlap detected between train and val splits!"
    assert not (train_paths & test_paths), "Data leakage: overlap detected between train and test splits!"
    assert not (val_paths & test_paths), "Data leakage: overlap detected between val and test splits!"

    return train_records, val_records, test_records

