
import csv
import math
import statistics
from pathlib import Path

filename = "wifi_bench_20261026_070019.csv"

if not Path(filename).exists():
    raise SystemExit("CSV file not found.")

axes = {
    "ax": [], "ay": [], "az": [],
    "gx": [], "gy": [], "gz": []
}

with open(filename, newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        for axis in axes:
            value = float(row[axis])

            if math.isfinite(value):
                axes[axis].append(value)

print("\nMPU6050 SENSOR ANALYSIS")
print("=" * 55)

for axis, values in axes.items():
    if not values:
        print(axis, "No valid measurements")
        continue

    print(f"\nAxis: {axis}")
    print(f"Minimum: {min(values):.4f}")
    print(f"Maximum: {max(values):.4f}")
    print(f"Mean: {statistics.mean(values):.4f}")
    print(f"Std Dev: {statistics.pstdev(values):.4f}")

print("\nAnalysis completed.")
