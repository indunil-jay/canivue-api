
import csv
from pathlib import Path

required = [
    "timestamp_ms", "ax", "ay", "az",
    "gx", "gy", "gz", "behaviour"
]

files = sorted(Path(".").glob("*.csv"))

if not files:
    print("No CSV files found.")

for file in files:
    print(f"\nChecking: {file.name}")

    with file.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if not set(required).issubset(reader.fieldnames or []):
            print("ERROR: Missing columns.")
            continue

        timestamps = []
        labels = set()
        invalid_rows = 0

        for row in reader:
            try:
                t = int(row["timestamp_ms"])
                for col in required[1:7]:
                    float(row[col])
                labels.add(row["behaviour"])
                timestamps.append(t)
            except (ValueError, TypeError):
                invalid_rows += 1

    print("Valid samples:", len(timestamps))
    print("Invalid rows:", invalid_rows)
    print("Behaviour labels:", labels)

    if len(timestamps) > 1:
        intervals = [
            b - a for a, b in zip(
                timestamps[:-1], timestamps[1:]
            )
        ]

        if any(d <= 0 for d in intervals):
            print("WARNING: Non-increasing timestamps")
            continue

        duration = (
            timestamps[-1] - timestamps[0]
        ) / 1000

        rate = (
            (len(timestamps) - 1) / duration
            if duration > 0 else 0
        )

        gaps = sum(d > 30 for d in intervals)

        print(f"Duration: {duration:.2f} seconds")
        print(f"Sampling rate: {rate:.2f} Hz")
        print("Gaps greater than 30 ms:", gaps)
