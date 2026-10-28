
import csv
import math
import random
from pathlib import Path

import numpy as np
from dataset_readiness import inspect_recording


# ==================================================
# 1. CONFIGURATION
# ==================================================

DATA_DIR = Path("data") / "raw"
OUTPUT_DIR = Path("data") / "processed"

WINDOW_SIZE = 256
STRIDE = 128
MIN_DOGS = 5
RANDOM_SEED = 42

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]

UNKNOWN_DOG_IDS = {"", "na", "n/a", "unknown", "none"}


# ==================================================
# 2. LOAD ELIGIBLE RECORDINGS
# ==================================================

def load_eligible_recording(path):
    report = inspect_recording(path)

    if report["quality_status"] != "PASS":
        print("Skipped: quality checks failed")
        return None

    if report["candidate_for_ml_review"] != "YES":
        print("Skipped: not eligible for ML review")
        return None

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        return None

    try:
        timestamps = np.array(
            [int(row["timestamp_ms"]) for row in rows],
            dtype=np.int64
        )

        signals = np.array(
            [
                [float(row[col]) for col in SENSOR_COLUMNS]
                for row in rows
            ],
            dtype=np.float32
        )

    except (ValueError, TypeError, KeyError):
        print("Skipped: invalid sensor values")
        return None

    if not np.isfinite(signals).all():
        print("Skipped: non-finite sensor values")
        return None

    labels = {row["behaviour"].strip() for row in rows}
    dog_ids = {row["dog_id"].strip() for row in rows}
    recording_ids = {
        row["recording_id"].strip() for row in rows
    }

    if (
        len(labels) != 1
        or len(dog_ids) != 1
        or len(recording_ids) != 1
    ):
        print("Skipped: inconsistent recording metadata")
        return None

    behaviour = next(iter(labels))
    dog_id = next(iter(dog_ids))
    recording_id = next(iter(recording_ids))

    if dog_id.casefold() in UNKNOWN_DOG_IDS:
        print("Skipped: missing dog ID")
        return None

    return {
        "timestamps": timestamps,
        "signals": signals,
        "behaviour": behaviour,
        "dog_id": dog_id,
        "recording_id": recording_id,
        "session_id": rows[0]["session_id"],
        "recording_start": rows[0]["recording_start"],
        "label_source": rows[0]["label_source"],
    }


# ==================================================
# 3. CREATE TIME WINDOWS
# ==================================================

def create_windows(recording):
    signals = recording["signals"]
    timestamps = recording["timestamps"]

    windows = []
    metadata = []

    for start in range(
        0,
        len(signals) - WINDOW_SIZE + 1,
        STRIDE
    ):
        end = start + WINDOW_SIZE

        window = signals[start:end]

        if window.shape != (WINDOW_SIZE, len(SENSOR_COLUMNS)):
            continue

        windows.append(window)

        metadata.append({
            "recording_id": recording["recording_id"],
            "dog_id": recording["dog_id"],
            "session_id": recording["session_id"],
            "recording_start": recording["recording_start"],
            "behaviour": recording["behaviour"],
            "label_source": recording["label_source"],
            "start_timestamp_ms": int(timestamps[start]),
            "end_timestamp_ms": int(timestamps[end - 1]),
        })

    return windows, metadata


# ==================================================
# 4. SPLIT BY DOG
# ==================================================

def split_by_dog(metadata):
    dog_ids = sorted({
        row["dog_id"].strip().casefold()
        for row in metadata
    })

    if len(dog_ids) < MIN_DOGS:
        print(
            f"Need at least {MIN_DOGS} distinct dogs for "
            "this initial train/validation/test workflow."
        )
        print("Distinct dogs available:", len(dog_ids))
        return None

    shuffled_dogs = dog_ids.copy()
    random.Random(RANDOM_SEED).shuffle(shuffled_dogs)

    n_dogs = len(shuffled_dogs)

    n_test = max(1, round(0.15 * n_dogs))
    n_val = max(1, round(0.15 * n_dogs))

    # Keep at least one dog in training.
    while n_test + n_val >= n_dogs:
        if n_val > 1:
            n_val -= 1
        elif n_test > 1:
            n_test -= 1
        else:
            print("Not enough dogs to create three splits.")
            return None

    test_dogs = set(shuffled_dogs[:n_test])
    val_dogs = set(
        shuffled_dogs[n_test:n_test + n_val]
    )
    train_dogs = set(
        shuffled_dogs[n_test + n_val:]
    )

    assignments = []

    for row in metadata:
        dog = row["dog_id"].strip().casefold()

        if dog in test_dogs:
            split = "test"
        elif dog in val_dogs:
            split = "validation"
        else:
            split = "train"

        assignments.append(split)

    print("\nDogs assigned to each split:")
    print("Train:", sorted(train_dogs))
    print("Validation:", sorted(val_dogs))
    print("Test:", sorted(test_dogs))

    return assignments


# ==================================================
# 5. PREPARE DATASET
# ==================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print("No CSV recordings found.")
        return

    all_windows = []
    all_metadata = []

    print("Checking recordings...")

    for path in files:
        recording = load_eligible_recording(path)

        if recording is None:
            print(f"Excluded: {path.name}")
            continue

        windows, metadata = create_windows(recording)

        all_windows.extend(windows)
        all_metadata.extend(metadata)

        print(
            f"Accepted: {path.name}, "
            f"{len(windows)} windows"
        )

    if not all_windows:
        print("\nNo eligible canine recordings found.")
        print("No ML dataset was created.")
        print(
            "Collect recordings with valid dog IDs, "
            "target behaviour labels and verified label sources."
        )
        return

    X = np.stack(all_windows).astype(np.float32)

    y = np.array(
        [row["behaviour"] for row in all_metadata],
        dtype=str
    )

    assignments = split_by_dog(all_metadata)

    if assignments is None:
        print("\nDataset preparation stopped.")
        print("Collect more independent dog recordings first.")
        return

    assignments = np.array(assignments)

    train_idx = np.where(assignments == "train")[0]
    val_idx = np.where(assignments == "validation")[0]
    test_idx = np.where(assignments == "test")[0]

    # Fit normalization using training data only.
    train_samples = X[train_idx].reshape(
        -1, len(SENSOR_COLUMNS)
    )

    mean = train_samples.mean(axis=0)
    std = train_samples.std(axis=0)

    # Avoid division by zero for constant channels.
    std[std == 0] = 1.0

    X_train = (X[train_idx] - mean) / std
    X_val = (X[val_idx] - mean) / std
    X_test = (X[test_idx] - mean) / std

    # Report behaviour coverage for every split.
    all_classes = set(y)

    print("\nDataset split summary:")

    for name, indices in [
        ("Train", train_idx),
        ("Validation", val_idx),
        ("Test", test_idx),
    ]:
        present = set(y[indices])
        missing = sorted(all_classes - present)

        print(f"\n{name}: {len(indices)} windows")
        print("Behaviours:", sorted(present))

        if missing:
            print("WARNING: Missing classes:", missing)

    # Save numerical arrays and training-only scaling parameters.
    np.savez_compressed(
        OUTPUT_DIR / "ml_dataset.npz",
        X_train=X_train.astype(np.float32),
        X_val=X_val.astype(np.float32),
        X_test=X_test.astype(np.float32),
        y_train=y[train_idx],
        y_val=y[val_idx],
        y_test=y[test_idx],
        mean=mean,
        std=std,
        feature_names=np.array(SENSOR_COLUMNS),
        window_size=np.array(WINDOW_SIZE),
        stride=np.array(STRIDE),
    )

    # Save the split assignment for traceability.
    metadata_path = OUTPUT_DIR / "ml_window_metadata.csv"

    with metadata_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        fieldnames = list(all_metadata[0].keys()) + ["split"]

        writer = csv.DictWriter(
            file, fieldnames=fieldnames
        )
        writer.writeheader()

        for row, split in zip(all_metadata, assignments):
            writer.writerow({**row, "split": split})

    print("\nSaved:", OUTPUT_DIR / "ml_dataset.npz")
    print("Saved:", metadata_path)
    print("Dataset preparation completed.")


if __name__ == "__main__":
    main()
