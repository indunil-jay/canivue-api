
import csv
import math
import statistics
from pathlib import Path


# ==================================================
# 1. CONFIGURATION
# ==================================================

DATA_DIR = Path("data") / "raw"
OUTPUT_DIR = Path("data") / "processed"

REPORT_PATH = OUTPUT_DIR / "dataset_readiness_report.csv"

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]

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

METADATA_COLUMNS = [
    "recording_id",
    "recording_start",
    "dog_id",
    "session_id",
    "behaviour",
    "label_source",
    "sensor_position",
    "target_sampling_rate_hz",
    "accelerometer_range",
    "gyroscope_range",
    "filter_bandwidth_hz",
]

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

UNKNOWN_DOG_IDS = {
    "", "NA", "N/A", "UNKNOWN", "NONE"
}

EXPECTED_HZ = 100
MIN_ACCEPTABLE_HZ = 90
MAX_ACCEPTABLE_HZ = 110
MAX_GAP_MS = 30
MIN_SAMPLES = 256

# Preliminary screening thresholds only.
# These do not prove that a behaviour label is incorrect.
STATIONARY_ACCEL_STD_REVIEW = 1.0
STATIONARY_GYRO_STD_REVIEW = 0.3


# ==================================================
# 2. INSPECT ONE RECORDING
# ==================================================

def inspect_recording(file_path):

    result = {
        "file": file_path.name,
        "recording_id": "",
        "dog_id": "",
        "session_id": "",
        "behaviour": "",
        "label_source": "",
        "samples": 0,
        "duration_seconds": 0.0,
        "sampling_rate_hz": 0.0,
        "invalid_rows": 0,
        "missing_metadata_rows": 0,
        "non_increasing_timestamps": 0,
        "gaps_over_30ms": 0,
        "max_accel_axis_std": 0.0,
        "max_gyro_axis_std": 0.0,
        "signal_review": "",
        "quality_status": "FAIL",
        "candidate_for_ml_review": "NO",
        "notes": "",
    }

    problems = []

    try:
        with file_path.open(
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(file)
            headers = reader.fieldnames or []

            missing_columns = [
                column for column in REQUIRED_COLUMNS
                if column not in headers
            ]

            if missing_columns:
                result["notes"] = (
                    "Missing columns: "
                    + ", ".join(missing_columns)
                )
                return result

            rows = list(reader)

    except (OSError, csv.Error) as error:
        result["notes"] = f"Cannot read file: {error}"
        return result

    if not rows:
        result["notes"] = "Empty recording"
        return result

    metadata_values = {
        column: set()
        for column in METADATA_COLUMNS
    }

    timestamps = []
    sensor_data = {
        column: [] for column in SENSOR_COLUMNS
    }

    invalid_rows = 0
    missing_metadata_rows = 0

    for row in rows:

        for column in METADATA_COLUMNS:
            metadata_values[column].add(
                (row.get(column) or "").strip()
            )

        if any(
            not (row.get(column) or "").strip()
            for column in METADATA_COLUMNS
        ):
            missing_metadata_rows += 1

        try:
            timestamp = int(row["timestamp_ms"])

            values = {
                column: float(row[column])
                for column in SENSOR_COLUMNS
            }

            if not all(
                math.isfinite(value)
                for value in values.values()
            ):
                raise ValueError("Non-finite sensor values")

        except (ValueError, TypeError, KeyError):
            invalid_rows += 1
            continue

        timestamps.append(timestamp)

        for column, value in values.items():
            sensor_data[column].append(value)

    result["invalid_rows"] = invalid_rows
    result["missing_metadata_rows"] = missing_metadata_rows
    result["samples"] = len(timestamps)

    # Read metadata only when each field has one consistent value.
    for column in METADATA_COLUMNS:
        values = metadata_values[column]

        if len(values) == 1:
            value = next(iter(values))

            if column in result:
                result[column] = value

    # Calculate timing statistics.
    if len(timestamps) >= 2:

        intervals = [
            current - previous
            for previous, current in zip(
                timestamps[:-1],
                timestamps[1:]
            )
        ]

        result["non_increasing_timestamps"] = sum(
            interval <= 0 for interval in intervals
        )

        result["gaps_over_30ms"] = sum(
            interval > MAX_GAP_MS for interval in intervals
        )

        duration = (
            timestamps[-1] - timestamps[0]
        ) / 1000

        result["duration_seconds"] = round(
            max(duration, 0), 2
        )

        if duration > 0:
            result["sampling_rate_hz"] = round(
                (len(timestamps) - 1) / duration,
                2
            )

    # Calculate signal variability for manual review.
    for axis_group, output_field in [
        (["ax", "ay", "az"], "max_accel_axis_std"),
        (["gx", "gy", "gz"], "max_gyro_axis_std"),
    ]:

        deviations = [
            statistics.pstdev(sensor_data[axis])
            for axis in axis_group
            if len(sensor_data[axis]) >= 2
        ]

        if deviations:
            result[output_field] = round(
                max(deviations), 4
            )

    # Flag unusually variable recordings labelled stationary.
    # This is a warning, not an automatic relabelling decision.
    if result["behaviour"] == "stationary_test":

        if (
            result["max_accel_axis_std"]
            > STATIONARY_ACCEL_STD_REVIEW
            or result["max_gyro_axis_std"]
            > STATIONARY_GYRO_STD_REVIEW
        ):
            result["signal_review"] = (
                "REVIEW: high variability for stationary label"
            )
        else:
            result["signal_review"] = (
                "No variability warning"
            )
    else:
        result["signal_review"] = (
            "No stationary-label check applied"
        )

    # Check recording metadata consistency.
    inconsistent_fields = [
        column
        for column, values in metadata_values.items()
        if len(values) != 1 or "" in values
    ]

    if inconsistent_fields:
        problems.append(
            "Inconsistent metadata: "
            + ", ".join(inconsistent_fields)
        )

    if invalid_rows:
        problems.append(f"{invalid_rows} invalid rows")

    if missing_metadata_rows:
        problems.append(
            f"{missing_metadata_rows} rows with missing metadata"
        )

    if len(timestamps) < MIN_SAMPLES:
        problems.append(
            f"Fewer than {MIN_SAMPLES} valid samples"
        )

    if result["non_increasing_timestamps"]:
        problems.append("Non-increasing timestamps detected")

    if result["gaps_over_30ms"]:
        problems.append("Timestamp gaps greater than 30 ms")

    rate = result["sampling_rate_hz"]

    if not MIN_ACCEPTABLE_HZ <= rate <= MAX_ACCEPTABLE_HZ:
        problems.append(
            f"Sampling rate outside "
            f"{MIN_ACCEPTABLE_HZ}-{MAX_ACCEPTABLE_HZ} Hz"
        )

    # A single behaviour label is required per recording.
    behaviours = metadata_values["behaviour"]

    if len(behaviours) != 1 or "" in behaviours:
        problems.append(
            "Missing or mixed behaviour labels"
        )

    result["quality_status"] = (
        "PASS" if not problems else "FAIL"
    )

    # Initial metadata gate for future canine ML data.
    dog_id = str(result["dog_id"]).strip().upper()
    behaviour = str(result["behaviour"]).strip()
    label_source = str(result["label_source"]).strip()

    candidate = (
        result["quality_status"] == "PASS"
        and behaviour in TARGET_BEHAVIOURS
        and dog_id not in UNKNOWN_DOG_IDS
        and label_source in VERIFIED_LABEL_SOURCES
    )

    result["candidate_for_ml_review"] = (
        "YES" if candidate else "NO"
    )

    if not candidate and not problems:

        if behaviour not in TARGET_BEHAVIOURS:
            problems.append("Not a target canine behaviour")

        if dog_id in UNKNOWN_DOG_IDS:
            problems.append("Missing valid dog ID")

        if label_source not in VERIFIED_LABEL_SOURCES:
            problems.append("Label source is not verified")

    result["notes"] = "; ".join(problems) if problems else "No basic issues detected"

    return result


# ==================================================
# 3. INSPECT THE DATASET
# ==================================================

def main():

    if not DATA_DIR.exists():
        print("Raw data directory not found:", DATA_DIR)
        return

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print("No CSV recordings found.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reports = []

    for file_path in files:
        report = inspect_recording(file_path)
        reports.append(report)

        print("\n" + "=" * 60)
        print("FILE:", report["file"])
        print("Behaviour:", report["behaviour"])
        print("Dog ID:", report["dog_id"])
        print("Samples:", report["samples"])
        print("Sampling rate:", report["sampling_rate_hz"], "Hz")
        print("Quality:", report["quality_status"])
        print("ML review candidate:", report["candidate_for_ml_review"])
        print("Signal review:", report["signal_review"])
        print("Notes:", report["notes"])

    # Save the detailed report.
    with REPORT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(reports[0].keys())
        )

        writer.writeheader()
        writer.writerows(reports)

    print("\n" + "=" * 60)
    print("DATASET READINESS SUMMARY")
    print("=" * 60)

    print("Recordings found:", len(reports))

    print(
        "Quality checks passed:",
        sum(r["quality_status"] == "PASS" for r in reports)
    )

    print(
        "Candidates for ML review:",
        sum(
            r["candidate_for_ml_review"] == "YES"
            for r in reports
        )
    )

    print("\nRecordings by behaviour:")

    behaviour_counts = {}

    for report in reports:
        label = report["behaviour"] or "MISSING"
        behaviour_counts[label] = (
            behaviour_counts.get(label, 0) + 1
        )

    for label, count in sorted(behaviour_counts.items()):
        print(f"  {label}: {count}")

    print("\nReport saved to:", REPORT_PATH)
    print("Readiness inspection completed.")


if __name__ == "__main__":
    main()
