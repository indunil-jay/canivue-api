"""Evaluate a trained ear checkpoint against a held-out test split.

Run as a module from the repo root:

    python -m ml.ear.evaluate --checkpoint model_registry/ear/model_best.pt \
        --data-dir /path/to/images

Reports the metrics from proposal Table 6 (accuracy, precision, recall, F1,
ROC-AUC, calibration error) using ml/common/metrics.py.
"""

import argparse

from ml.common.metrics import classification_metrics, expected_calibration_error
from ml.ear.dataset import (
    LABELS,
    CanineEarDataset,
    get_eval_transforms,
    load_labels_csv,
)
from ml.ear.model import build_model
from ml.ear.splitting import stratified_train_val_test_split


def evaluate(checkpoint_path: str, data_dir: str, labels_csv: str, seed: int = 42) -> None:
    import torch
    from torch.utils.data import DataLoader

    records = load_labels_csv(labels_csv)
    # Same stratified split + seed as train.py, so this is the genuine held-out test set.
    _train, _val, test_records = stratified_train_val_test_split(
        records, ratios=(0.70, 0.15, 0.15), seed=seed
    )
    test_ds = CanineEarDataset(data_dir, test_records, transform=get_eval_transforms())
    test_loader = DataLoader(test_ds, batch_size=32)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(num_classes=len(LABELS), pretrained=False).to(device)
    ckpt = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt)
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
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    evaluate(args.checkpoint, args.data_dir, args.labels_csv, args.seed)
