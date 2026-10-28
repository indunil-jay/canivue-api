
import csv
from pathlib import Path

import numpy as np

output_dir = Path("data") / "processed"

dataset_path = output_dir / "sensor_windows.npz"
metadata_path = output_dir / "window_metadata.csv"

if not dataset_path.exists():
    raise SystemExit("Preprocessed dataset not found.")

with np.load(dataset_path, allow_pickle=False) as data:
    X = data["X"]
    y = data["y"]
    eligible = data["eligible_for_behavior_model"]
    features = data["feature_names"]

    print("PREPROCESSED DATASET INSPECTION")
    print("=" * 45)
    print("X shape:", X.shape)
    print("Labels shape:", y.shape)
    print("Eligibility shape:", eligible.shape)
    print("Features:", features.tolist())
    print("Data type:", X.dtype)
    print("All values finite:", np.isfinite(X).all())
    print("Unique labels:", np.unique(y).tolist())
    print("Eligible windows:", int(eligible.sum()))
    print("Excluded windows:", int((~eligible).sum()))

if metadata_path.exists():
    with metadata_path.open(
        newline="",
        encoding="utf-8"
    ) as file:
        rows = list(csv.DictReader(file))

    print("\nMetadata rows:", len(rows))
    print("Metadata matches window count:", len(rows) == len(X))
else:
    print("Metadata file not found.")
