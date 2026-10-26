
import socket
import csv
import time
from datetime import datetime

HOST = "192.168.4.1"
PORT = 5000
DURATION = 30

# Bench-test data is not a verified dog behaviour
LABEL = "unverified_motion"

filename = (
    "wifi_bench_" +
    datetime.now().strftime("%Y%m%d_%H%M%S") +
    ".csv"
)

columns = [
    "timestamp_ms", "ax", "ay", "az",
    "gx", "gy", "gz", "behaviour"
]

samples = 0
buffer = b""

try:
    print("Connecting to ESP32...")

    with socket.create_connection(
        (HOST, PORT), timeout=10
    ) as connection:

        connection.settimeout(1.0)

        print("Connected successfully!")
        print("Recording for 30 seconds...")

        start = time.monotonic()

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)

            while time.monotonic() - start < DURATION:
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
                        timestamp = int(values[0])
                        measurements = [
                            float(x) for x in values[1:]
                        ]
                    except ValueError:
                        continue

                    writer.writerow([
                        timestamp,
                        *measurements,
                        LABEL
                    ])
                    samples += 1

    print("\nRecording finished.")
    print("File:", filename)
    print("Samples:", samples)

except OSError as error:
    print("Connection error:", error)
    print("Check your laptop Wi-Fi connection.")
