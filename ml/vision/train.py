"""Training entrypoint for the EfficientNet visual-condition classifier.

Run as a module from the repo root (so both the sibling `dataset.py` and the
shared `ml.common` package resolve correctly):

    python -m ml.vision.train --data-dir /path/to/images --epochs 20 \
        --out model_registry/vision/efficientnet_v1.pt

Writes a `state_dict` checkpoint intended to be loaded by a future
`app/features/vision_diagnosis/infrastructure/ml/engine.py` serving engine
(see `.agents/skills/ml-feature/SKILL.md`).
"""

import argparse

from ml.common.data_splitting import train_val_test_split
from ml.vision.dataset import LABELS, CanineVisionDataset, load_labels_csv


def build_model(num_classes: int):
    import torch
    from torchvision import models

    model = models.efficientnet_b0(weights="IMAGENET1K_V1")  # transfer learning (proposal §5.7.1)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)
    return model


def train(data_dir: str, labels_csv: str, epochs: int, batch_size: int, lr: float, out_path: str) -> None:
    import torch
    from torch.utils.data import DataLoader

    records = load_labels_csv(labels_csv)
    train_records, val_records, _test_records = train_val_test_split(records, pet_id_key="pet_id")

    train_ds = CanineVisionDataset(data_dir, train_records)
    val_ds = CanineVisionDataset(data_dir, val_records)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(num_classes=len(LABELS)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                preds = model(images).argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        val_acc = correct / total if total else 0.0
        print(f"epoch {epoch + 1}/{epochs}  loss={running_loss / max(len(train_loader), 1):.4f}  val_acc={val_acc:.4f}")

    torch.save(model.state_dict(), out_path)
    print(f"Saved checkpoint to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Directory containing the training images")
    parser.add_argument("--labels-csv", default="labels.csv", help="CSV: image_path,pet_id,label")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--out", default="model_registry/vision/efficientnet_v1.pt")
    args = parser.parse_args()

    train(args.data_dir, args.labels_csv, args.epochs, args.batch_size, args.lr, args.out)
