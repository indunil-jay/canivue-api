"""Evaluate a trained vision checkpoint against a held-out test split.

Run as a module from the repo root:

    python -m ml.vision.evaluate --checkpoint model_registry/vision/efficientnet_v1.pt \
        --data-dir /path/to/images

Reports the metrics from proposal Table 6 (accuracy, precision, recall, F1,
ROC-AUC, calibration error) using ml/common/metrics.py.
"""

import argparse

from ml.common.data_splitting import train_val_test_split
from ml.common.metrics import classification_metrics, expected_calibration_error
from ml.vision.dataset import LABELS, CanineVisionDataset, load_labels_csv
from ml.vision.train import build_model


def evaluate(checkpoint_path: str, data_dir: str, labels_csv: str) -> None:
    import torch
    from torch.utils.data import DataLoader

    records = load_labels_csv(labels_csv)
    _train_records, _val_records, test_records = train_val_test_split(records, pet_id_key="pet_id")
    test_ds = CanineVisionDataset(data_dir, test_records)
    test_loader = DataLoader(test_ds, batch_size=32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(num_classes=len(LABELS)).to(device)
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()

    y_true, y_pred, top_confidences = [], [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            probs = torch.softmax(model(images), dim=1)
            preds = probs.argmax(dim=1)
            y_true.extend(labels.tolist())
            y_pred.extend(preds.cpu().tolist())
            top_confidences.extend(probs.max(dim=1).values.cpu().tolist())

    metrics = classification_metrics(y_true, y_pred)
    correctness = [int(t == p) for t, p in zip(y_true, y_pred)]
    metrics["expected_calibration_error"] = expected_calibration_error(correctness, top_confidences)

    for name, value in metrics.items():
        print(f"{name}: {value:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--labels-csv", default="labels.csv")
    args = parser.parse_args()

    evaluate(args.checkpoint, args.data_dir, args.labels_csv)
