
import csv
import math
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

DATA_DIR = Path("data") / "raw"
OUTPUT_DIR = Path("data") / "processed"

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]


def load_recording(path):
    timestamps = []
    measurements = {axis: [] for axis in SENSOR_COLUMNS}

    with path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)

        required = {"timestamp_ms", *SENSOR_COLUMNS}

        if not required.issubset(reader.fieldnames or []):
            print(f"Skipping {path.name}: missing sensor columns")
            return None

        for row in reader:
            try:
                timestamp = int(row["timestamp_ms"])
                values = {
                    axis: float(row[axis])
                    for axis in SENSOR_COLUMNS
                }

                if not all(math.isfinite(v) for v in values.values()):
                    continue

                timestamps.append(timestamp)

                for axis, value in values.items():
                    measurements[axis].append(value)

            except (ValueError, TypeError, KeyError):
                continue

    if len(timestamps) < 2:
        print(f"Skipping {path.name}: insufficient valid samples")
        return None

    # Convert timestamps to seconds relative to the first sample.
    time_s = [
        (timestamp - timestamps[0]) / 1000
        for timestamp in timestamps
    ]

    duration = time_s[-1]

    if duration <= 0:
        print(f"Skipping {path.name}: invalid timestamps")
        return None

    return time_s, measurements, duration


def analyze_recording(path):
    result = load_recording(path)

    if result is None:
        return

    time_s, data, duration = result
    sample_count = len(time_s)
    sampling_rate = (sample_count - 1) / duration

    print("\n" + "=" * 60)
    print("FILE:", path.name)
    print("Samples:", sample_count)
    print(f"Duration: {duration:.2f} seconds")
    print(f"Measured sampling rate: {sampling_rate:.2f} Hz")

    for axis, values in data.items():
        print(f"\n{axis.upper()}")
        print(f"  Minimum: {min(values):.4f}")
        print(f"  Maximum: {max(values):.4f}")
        print(f"  Mean: {statistics.mean(values):.4f}")
        print(f"  Std Dev: {statistics.pstdev(values):.4f}")

    acceleration_magnitude = [
        math.sqrt(ax**2 + ay**2 + az**2)
        for ax, ay, az in zip(
            data["ax"], data["ay"], data["az"]
        )
    ]

    gyro_magnitude = [
        math.sqrt(gx**2 + gy**2 + gz**2)
        for gx, gy, gz in zip(
            data["gx"], data["gy"], data["gz"]
        )
    ]

    print(
        "\nMean acceleration magnitude:",
        f"{statistics.mean(acceleration_magnitude):.4f} m/s^2"
    )

    print(
        "Mean gyroscope magnitude:",
        f"{statistics.mean(gyro_magnitude):.4f} rad/s"
    )

    # Plot the three acceleration axes.
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for axis in ["ax", "ay", "az"]:
        axes[0].plot(time_s, data[axis], label=axis)

    axes[0].set_title(f"Acceleration: {path.stem}")
    axes[0].set_ylabel("Acceleration (m/s²)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot the three gyroscope axes.
    for axis in ["gx", "gy", "gz"]:
        axes[1].plot(time_s, data[axis], label=axis)

    axes[1].set_title("Angular velocity")
    axes[1].set_xlabel("Time (seconds)")
    axes[1].set_ylabel("Angular velocity (rad/s)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()

    output_path = OUTPUT_DIR / f"{path.stem}_signals.png"
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    print("Graph saved to:", output_path)


def main():
    if not DATA_DIR.exists():
        print("Data directory not found:", DATA_DIR)
        print("Run this script from the data_logger directory.")
        return

    files = sorted(DATA_DIR.glob("*.csv"))

    if not files:
        print("No CSV files found in:", DATA_DIR)
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in files:
        analyze_recording(path)

    print("\nAnalysis completed.")


if __name__ == "__main__":
    main()
