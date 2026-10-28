import csv
from collections import Counter
from pathlib import Path

import numpy as np


# ==================================================
# 1. CONFIGURATION
# ==================================================

DATA_DIR = Path("data") / "raw"
OUTPUT_DIR = Path("data") / "processed"

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]

WINDOW_SIZE = 256
STRIDE = 128
MAX_GAP_MS = 30

TARGET_BEHAVIOURS = {
    "rest",
    "walking",
    "running",
    "scratching",
    "head_shaking",
}

VERIFIED_LABEL_SOURCES = {
    "direct_observation",
    "video_verified",
}

REQUIRED_COLUMNS = [
    "recording_id",
    "recording_start",
    "dog_id",
    "session_id",
    "timestamp_ms",
    *SENSOR_COLUMNS,
    "behaviour",
    "label_source",
    "sensor_position",
    "target_sampling_rate_hz",
    "accelerometer_range",
    "gyroscope_range",
    "filter_bandwidth_hz",
]


# ==================================================
# 2. LOAD AND CHECK ONE RECORDING
# ==================================================

def load_recording(file_path):

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)
        headers = reader.fieldnames or []

        missing = [
            column
            for column in REQUIRED_COLUMNS
            if column not in headers
        ]

        if missing:
            print(f"SKIPPED: {file_path.name}")
            print("Missing columns:", missing)
            return None

        rows = list(reader)

    if not rows:
        print(f"SKIPPED: Empty file {file_path.name}")
        return None

    timestamps = []
    measurements = []
    behaviours = []

    for row in rows:

        try:
            timestamp = int(row["timestamp_ms"])

            values = [
                float(row[column])
                for column in SENSOR_COLUMNS
            ]

        except (ValueError, TypeError, KeyError):
            print(f"SKIPPED: Invalid values in {file_path.name}")
            return None

        if not np.isfinite(values).all():
            print(f"SKIPPED: Non-finite values in {file_path.name}")
            return None

        if not row["behaviour"].strip():
            print(f"SKIPPED: Missing behaviour label in {file_path.name}")
            return None

        timestamps.append(timestamp)
        measurements.append(values)
        behaviours.append(row["behaviour"].strip())

    timestamps = np.asarray(timestamps, dtype=np.int64)
    measurements = np.asarray(measurements, dtype=np.float32)

    # Check timestamp order and large gaps.
    intervals = np.diff(timestamps)

    if np.any(intervals <= 0):
        print(f"SKIPPED: Non-increasing timestamps in {file_path.name}")
        return None

    if np.any(intervals > MAX_GAP_MS):
        print(f"SKIPPED: Large timestamp gaps in {file_path.name}")
        return None

    # Check recording metadata is consistent.
    metadata_columns = [
        "recording_id",
        "recording_start",
        "dog_id",
        "session_id",
        "label_source",
        "sensor_position",
        "target_sampling_rate_hz",
        "accelerometer_range",
        "gyroscope_range",
        "filter_bandwidth_hz",
    ]

    for column in metadata_columns:
        values = {row[column].strip() for row in rows}

        if len(values) != 1 or "" in values:
            print(
                f"SKIPPED: Inconsistent or missing "
                f"{column} in {file_path.name}"
            )
            return None

    if len(set(behaviours)) != 1:
        print(
            f"SKIPPED: Multiple behaviour labels in "
            f"{file_path.name}. Split labels into separate "
            f"recordings before preprocessing."
        )
        return None

    return {
        "timestamps": timestamps,
        "measurements": measurements,
        "behaviour": behaviours[0],
        "metadata": rows[0],
    }


# ==================================================
# 3. DETERMINE ML ELIGIBILITY
# ==================================================

def check_ml_eligibility(metadata, behaviour):

    dog_id = metadata["dog_id"].strip()
    label_source = metadata["label_source"].strip()

    if behaviour not in TARGET_BEHAVIOURS:
        return False, "Engineering test or non-target label"

    if dog_id.upper() in {"", "NA", "N/A", "UNKNOWN"}:
        return False, "Missing dog ID"

    if label_source not in VERIFIED_LABEL_SOURCES:
        return False, "Behaviour label not verified"

    return True, "Eligible for further ML dataset review"


# ==================================================
# 4. CREATE OVERLAPPING WINDOWS
# ==================================================

def create_windows(recording, file_path):

    timestamps = recording["timestamps"]
    measurements = recording["measurements"]
    behaviour = recording["behaviour"]
    metadata = recording["metadata"]

    windows = []
    labels = []
    eligibility_flags = []
    metadata_rows = []

    eligible, reason = check_ml_eligibility(
        metadata,
        behaviour
    )

    recording_id = metadata["recording_id"]

    window_number = 0

    for start in range(
        0,
        len(measurements) - WINDOW_SIZE + 1,
        STRIDE
    ):

        end = start + WINDOW_SIZE

        window_data = measurements[start:end]
        window_timestamps = timestamps[start:end]

        # Confirm every window contains the expected
        # number of samples.
        if len(window_data) != WINDOW_SIZE:
            continue

        window_number += 1

        windows.append(window_data)
        labels.append(behaviour)
        eligibility_flags.append(eligible)

        metadata_rows.append({
            "window_id": f"{recording_id}_W{window_number:04d}",
            "recording_id": recording_id,
            "recording_start": metadata["recording_start"],
            "dog_id": metadata["dog_id"],
            "session_id": metadata["session_id"],
            "behaviour": behaviour,
            "label_source": metadata["label_source"],
            "sensor_position": metadata["sensor_position"],
            "start_timestamp_ms": int(window_timestamps[0]),
            "end_timestamp_ms": int(window_timestamps[-1]),
            "sample_count": len(window_data),
            "eligible_for_behavior_model": eligible,
            "eligibility_reason": reason,
        })

    print(
        f"{file_path.name}: "
        f"{window_number} windows created"
    )

    return windows, labels, eligibility_flags, metadata_rows


# ==================================================
# 5. PROCESS ALL RECORDINGS
# ==================================================

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print("No CSV recordings found in:", DATA_DIR)
        return

    all_windows = []
    all_labels = []
    all_eligibility = []
    all_metadata = []

    for file_path in files:

        print(f"\nProcessing: {file_path.name}")

        recording = load_recording(file_path)

        if recording is None:
            continue

        result = create_windows(
            recording,
            file_path
        )

        windows, labels, eligibility, metadata = result

        all_windows.extend(windows)
        all_labels.extend(labels)
        all_eligibility.extend(eligibility)
        all_metadata.extend(metadata)

    if not all_windows:
        print("\nNo valid windows were created.")
        return

    # Shape: (number of windows, 256 samples, 6 channels)
    X = np.stack(all_windows).astype(np.float32)

    y = np.asarray(all_labels, dtype=str)

    eligible_array = np.asarray(
        all_eligibility,
        dtype=bool
    )

    # Save the time-series windows.
    np.savez_compressed(
        OUTPUT_DIR / "sensor_windows.npz",
        X=X,
        y=y,
        eligible_for_behavior_model=eligible_array,
        feature_names=np.asarray(SENSOR_COLUMNS),
    )

    # Save window-level metadata.
    metadata_path = OUTPUT_DIR / "window_metadata.csv"

    with metadata_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(all_metadata[0].keys())
        )

        writer.writeheader()
        writer.writerows(all_metadata)

    print("\n" + "=" * 55)
    print("PREPROCESSING SUMMARY")
    print("=" * 55)

    print("Total windows:", len(X))
    print("Window shape:", X.shape)
    print("Channels:", SENSOR_COLUMNS)
    print("Samples per window:", WINDOW_SIZE)
    print("Window duration:", WINDOW_SIZE / 100, "seconds")
    print("Step between windows:", STRIDE / 100, "seconds")

    print("\nWindows per label:")

    for label, count in Counter(y).items():
        print(f"  {label}: {count}")

    print(
        "\nWindows eligible for further ML review:",
        int(eligible_array.sum())
    )

    print(
        "Engineering or unverified windows:",
        int((~eligible_array).sum())
    )

    print("\nSaved files:")
    print(OUTPUT_DIR / "sensor_windows.npz")
    print(metadata_path)

    print("\nPreprocessing completed.")


if __name__ == "__main__":
    main()