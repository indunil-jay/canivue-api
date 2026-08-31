"""Dog-level dataset splitting.

Proposal §5.6: "Dataset splitting: dog-level separation between training,
validation, and test sets to prevent leakage across repeated observations
from the same dog." A naive random row-level split would let the same dog's
photos/sensor sessions appear in both train and test, inflating reported
accuracy. Split on the dog/pet ID first, then take every record for the
dogs assigned to each split.
"""

import hashlib
from typing import Dict, List, Sequence, Tuple

DEFAULT_SPLIT_RATIOS: Dict[str, float] = {"train": 0.7, "val": 0.15, "test": 0.15}


def split_pet_ids(
    pet_ids: Sequence[str],
    ratios: Dict[str, float] = DEFAULT_SPLIT_RATIOS,
    seed: int = 42,
) -> Dict[str, List[str]]:
    """Deterministically assign each unique pet ID to exactly one split.

    Uses a salted hash instead of `random.shuffle` so the assignment is
    stable across runs/machines given the same `seed`, without needing to
    persist a split file.
    """
    if abs(sum(ratios.values()) - 1.0) > 1e-6:
        raise ValueError(f"Split ratios must sum to 1.0, got {ratios}")

    unique_ids = sorted(set(pet_ids))
    buckets: Dict[str, List[str]] = {name: [] for name in ratios}

    for pet_id in unique_ids:
        digest = hashlib.sha256(f"{seed}:{pet_id}".encode()).hexdigest()
        # Map the hash to [0, 1) deterministically.
        fraction = int(digest[:8], 16) / 0xFFFFFFFF

        cumulative = 0.0
        for split_name, ratio in ratios.items():
            cumulative += ratio
            if fraction <= cumulative:
                buckets[split_name].append(pet_id)
                break
        else:
            buckets[next(iter(ratios))].append(pet_id)

    return buckets


def filter_records_by_split(
    records: Sequence[dict], pet_id_key: str, split_pet_ids_for_target: List[str]
) -> List[dict]:
    """Keep only records whose pet ID falls in the given split's pet-ID list."""
    allowed = set(split_pet_ids_for_target)
    return [r for r in records if r[pet_id_key] in allowed]


def train_val_test_split(
    records: Sequence[dict],
    pet_id_key: str = "pet_id",
    ratios: Dict[str, float] = DEFAULT_SPLIT_RATIOS,
    seed: int = 42,
) -> Tuple[List[dict], List[dict], List[dict]]:
    """Convenience wrapper: split a list of record dicts into (train, val, test)."""
    pet_ids = [r[pet_id_key] for r in records]
    buckets = split_pet_ids(pet_ids, ratios=ratios, seed=seed)
    return (
        filter_records_by_split(records, pet_id_key, buckets["train"]),
        filter_records_by_split(records, pet_id_key, buckets["val"]),
        filter_records_by_split(records, pet_id_key, buckets["test"]),
    )
