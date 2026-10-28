
import csv
import socket
from datetime import datetime
from pathlib import Path
import time

HOST = "192.168.4.1"
PORT = 5000
TARGET_HZ = 100

ACCEL_RANGE = "+/-8g"
GYRO_RANGE = "+/-1000 deg/s"
FILTER_BANDWIDTH_HZ = 44

VALID_BEHAVIOURS = {
    "stationary_test",
    "manual_motion_test",
    "unverified_motion",
    "rest",
    "walking",
    "running",
    "scratching",
    "head_shaking",
}

DOG_BEHAVIOURS = {
    "rest",
    "walking",
    "running",
    "scratching",
    "head_shaking",
}

VALID_LABEL_SOURCES = {
    "engineering_test",
    "direct_observation",
    "video_verified",
}


def ask(prompt, default=None):
    value = input(prompt).strip()
    return value if value else default


behaviour = ask(
    "Behaviour label "
    "(stationary_test/manual_motion_test/rest/walking/"
    "running/scratching/head_shaking): "
).lower().replace(" ", "_")

if behaviour not in VALID_BEHAVIOURS:
    raise SystemExit("Invalid behaviour label.")

dog_id = ask("Dog ID (enter NA for bench testing): ", "NA")
session_id = ask("Session ID: ", "S001")
sensor_position = ask("Sensor position [bench]: ", "bench")

label_source = ask(
    "Label source (engineering_test/direct_observation/"
    "video_verified): ",
    "engineering_test",
).lower()

if label_source not in VALID_LABEL_SOURCES:
    raise SystemExit("Invalid label source.")

if behaviour in DOG_BEHAVIOURS:
    if dog_id == "NA":
        raise SystemExit(
            "Dog behaviour recordings require a dog ID."
        )

    if label_source == "engineering_test":
        raise SystemExit(
            "Dog behaviour labels require observation "
            "or video verification."
        )

duration_text = ask("Duration in seconds [30]: ", "30")

try:
    duration = int(duration_text)
    if duration <= 0:
        raise ValueError
except ValueError:
    raise SystemExit("Duration must be a positive integer.")

recording_start = datetime.now().astimezone()
recording_id = (
    behaviour + "_" +
    recording_start.strftime("%Y%m%d_%H%M%S")
)

output_dir = Path("data") / "raw"
output_dir.mkdir(parents=True, exist_ok=True)

filename = output_dir / f"{recording_id}.csv"

columns = [
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

samples = 0
buffer = b""

try:
    print(f"\nConnecting to {HOST}:{PORT}...")

    with socket.create_connection(
        (HOST, PORT), timeout=10
    ) as connection:

        connection.settimeout(1.0)

        print("Connected to ESP32.")
        print(f"Recording {behaviour} for {duration} seconds.")
        print(f"Output file: {filename}")

        start = time.monotonic()

        with filename.open(
            "w", newline="", encoding="utf-8"
        ) as file:

            writer = csv.writer(file)
            writer.writerow(columns)

            while time.monotonic() - start < duration:
                try:
                    packet = connection.recv(4096)
                except socket.timeout:
                    continue

                if not packet:
                    print("ESP32 disconnected.")
                    break

                buffer += packet

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    values = line.decode(
                        "utf-8", errors="ignore"
                    ).strip().split(",")

                    if len(values) != 7:
                        continue

                    try:
                        timestamp_ms = int(values[0])
                        measurements = [
                            float(v) for v in values[1:]
                        ]
                    except ValueError:
                        continue

                    writer.writerow([
                        recording_id,
                        recording_start.isoformat(),
                        dog_id,
                        session_id,
                        timestamp_ms,
                        *measurements,
                        behaviour,
                        label_source,
                        sensor_position,
                        TARGET_HZ,
                        ACCEL_RANGE,
                        GYRO_RANGE,
                        FILTER_BANDWIDTH_HZ,
                    ])

                    samples += 1

    print("\nRecording completed.")
    print("File:", filename)
    print("Valid samples received:", samples)

    if samples == 0:
        print("WARNING: No valid sensor samples received.")

except OSError as error:
    print("\nConnection error:", error)
    print("Check ESP32 power, Wi-Fi, and IP address.")
