
import csv
import math
from pathlib import Path

DATA_DIR = Path("data") / "raw"

REQUIRED_COLUMNS = [
    "recording_id",
    "recording_start",
    "dog_id",
    "session_id",
    "timestamp_ms",
    "ax", "ay", "az",
    "gx", "gy", "gz",
    "behaviour",
    "label_source",
    "sensor_position",
    "target_sampling_rate_hz",
    "accelerometer_range",
    "gyroscope_range",
    "filter_bandwidth_hz",
]

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]


def validate_file(file_path):
    print(f"\nChecking: {file_path}")

    timestamps = []
    labels = set()
    invalid_rows = 0
    missing_metadata = 0
    recording_ids = set()
    session_ids = set()

    with file_path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        headers = reader.fieldnames or []
        missing_columns = [
            col for col in REQUIRED_COLUMNS
            if col not in headers
        ]

        if missing_columns:
            print("Missing columns:", missing_columns)
            return

        for row in reader:
            try:
                timestamp = int(row["timestamp_ms"])

                values = [
                    float(row[col])
                    for col in SENSOR_COLUMNS
                ]

                if not all(math.isfinite(v) for v in values):
                    raise ValueError("Non-finite sensor value")

                if not row["behaviour"].strip():
                    raise ValueError("Missing behaviour label")

                timestamps.append(timestamp)
                labels.add(row["behaviour"])
                recording_ids.add(row["recording_id"])
                session_ids.add(row["session_id"])

                metadata_columns = [
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

                if any(
                    not row[col].strip()
                    for col in metadata_columns
                ):
                    missing_metadata += 1

            except (ValueError, TypeError, KeyError):
                invalid_rows += 1

    print("Valid samples:", len(timestamps))
    print("Invalid rows:", invalid_rows)
    print("Missing metadata rows:", missing_metadata)
    print("Behaviour labels:", labels)
    print("Recording IDs:", recording_ids)
    print("Session IDs:", session_ids)

    if len(timestamps) < 2:
        print("Not enough valid samples to assess timing.")
        return

    intervals = [
        current - previous
        for previous, current in zip(
            timestamps[:-1], timestamps[1:]
        )
    ]

    non_increasing = sum(
        interval <= 0 for interval in intervals
    )

    positive_intervals = [
        interval for interval in intervals
        if interval > 0
    ]

    duration = (
        timestamps[-1] - timestamps[0]
    ) / 1000

    if duration > 0:
        rate = (len(timestamps) - 1) / duration
        print(f"Duration: {duration:.2f} seconds")
        print(f"Sampling rate: {rate:.2f} Hz")
    else:
        print("Cannot calculate sampling rate.")

    print("Non-increasing timestamps:", non_increasing)

    gaps = sum(
        interval > 30 for interval in positive_intervals
    )

    print("Gaps greater than 30 ms:", gaps)

    if (
        invalid_rows == 0
        and missing_metadata == 0
        and non_increasing == 0
    ):
        print("Basic data validation: PASSED")
    else:
        print("Basic data validation: CHECK REQUIRED")


def main():
    if not DATA_DIR.exists():
        print(f"Directory not found: {DATA_DIR}")
        print("Run this script from the data_logger directory.")
        return

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print(f"No CSV files found in {DATA_DIR}")
        return

    for file_path in files:
        validate_file(file_path)


if __name__ == "__main__":
    main()
