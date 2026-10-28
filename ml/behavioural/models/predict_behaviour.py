
import argparse
import csv
from pathlib import Path

import numpy as np
import torch

from behaviour_cnn_lstm import BehaviourCNNLSTM


# ==================================================
# 1. CONFIGURATION
# ==================================================

WINDOW_SIZE = 256
STRIDE = 128

SENSOR_COLUMNS = ["ax", "ay", "az", "gx", "gy", "gz"]

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "behaviour_cnn_lstm_best.pt"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ==================================================
# 2. LOAD TRAINED MODEL
# ==================================================

def load_model():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained checkpoint not found: {MODEL_PATH}\n"
            "Train the model using verified canine data first."
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True,
    )

    required = [
        "model_state_dict",
        "classes",
        "normalization_mean",
        "normalization_std",
    ]

    missing = [
        key for key in required
        if key not in checkpoint
    ]

    if missing:
        raise ValueError(
            f"Checkpoint is missing: {missing}. "
            "Retrain using the updated training script."
        )

    classes = checkpoint["classes"]

    mean = np.asarray(
        checkpoint["normalization_mean"],
        dtype=np.float32,
    )

    std = np.asarray(
        checkpoint["normalization_std"],
        dtype=np.float32,
    )

    if mean.shape != (6,) or std.shape != (6,):
        raise ValueError("Invalid normalization dimensions.")

    if (
        not np.isfinite(mean).all()
        or not np.isfinite(std).all()
        or np.any(std <= 0)
    ):
        raise ValueError("Invalid normalization values.")

    model = BehaviourCNNLSTM(
        input_channels=6,
        num_classes=len(classes),
    ).to(DEVICE)

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    return model, classes, mean, std


# ==================================================
# 3. READ SENSOR CSV
# ==================================================

def read_sensor_csv(file_path):

    if not file_path.exists():
        raise FileNotFoundError(
            f"Sensor CSV not found: {file_path}"
        )

    measurements = []

    with file_path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        reader = csv.DictReader(file)

        headers = reader.fieldnames or []

        missing = [
            column for column in SENSOR_COLUMNS
            if column not in headers
        ]

        if missing:
            raise ValueError(
                f"CSV is missing sensor columns: {missing}"
            )

        for line_number, row in enumerate(reader, start=2):

            try:
                values = [
                    float(row[column])
                    for column in SENSOR_COLUMNS
                ]
            except (ValueError, TypeError, KeyError):
                raise ValueError(
                    f"Invalid sensor values at CSV line "
                    f"{line_number}"
                )

            if not np.isfinite(values).all():
                raise ValueError(
                    f"Non-finite values at CSV line "
                    f"{line_number}"
                )

            measurements.append(values)

    if not measurements:
        raise ValueError("The sensor CSV contains no data.")

    return np.asarray(
        measurements,
        dtype=np.float32,
    )


# ==================================================
# 4. CREATE SENSOR WINDOWS
# ==================================================

def create_windows(measurements):

    if len(measurements) < WINDOW_SIZE:
        raise ValueError(
            f"Need at least {WINDOW_SIZE} samples. "
            f"Received {len(measurements)}."
        )

    windows = []
    start_indices = []

    for start in range(
        0,
        len(measurements) - WINDOW_SIZE + 1,
        STRIDE,
    ):
        windows.append(
            measurements[start:start + WINDOW_SIZE]
        )

        start_indices.append(start)

    return (
        np.stack(windows).astype(np.float32),
        start_indices,
    )


# ==================================================
# 5. PREDICT EACH WINDOW
# ==================================================

def predict(model, classes, mean, std, windows):

    # Use the same training-only normalization values.
    normalized = (windows - mean) / std

    X = torch.from_numpy(
        normalized.astype(np.float32)
    ).to(DEVICE)

    with torch.no_grad():
        logits = model(X)
        probabilities = torch.softmax(logits, dim=1)

    probabilities = probabilities.cpu().numpy()

    return probabilities


# ==================================================
# 6. MAIN
# ==================================================

def main():

    parser = argparse.ArgumentParser(
        description="Predict behaviour classes from sensor CSV data."
    )

    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to a sensor CSV recording",
    )

    args = parser.parse_args()

    try:
        model, classes, mean, std = load_model()

        measurements = read_sensor_csv(
            args.csv_file
        )

        windows, start_indices = create_windows(
            measurements
        )

        probabilities = predict(
            model,
            classes,
            mean,
            std,
            windows,
        )

    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Cannot run inference: {error}")

    print("CANIVUE SENSOR INFERENCE")
    print("=" * 50)
    print("Recording:", args.csv_file.name)
    print("Windows:", len(windows))
    print("Device:", DEVICE)

    for index, (start, scores) in enumerate(
        zip(start_indices, probabilities),
        start=1,
    ):
        predicted_index = int(np.argmax(scores))

        predicted_class = classes[predicted_index]
        confidence = float(scores[predicted_index])

        print(
            f"Window {index:03d} | "
            f"Samples {start}-{start + WINDOW_SIZE - 1} | "
            f"Prediction: {predicted_class} | "
            f"Confidence: {confidence:.3f}"
        )

    print("\nInference completed.")
    print(
        "Predictions are experimental outputs, "
        "not veterinary diagnoses."
    )


if __name__ == "__main__":
    main()
