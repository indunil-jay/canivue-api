"""Two-stage training entrypoint for the Canine Ear Disease Classification model.

Implements transfer learning with an EfficientNet-B0 backbone:
- Stage A: Head training with frozen backbone.
- Stage B: Fine-tuning top convolutional blocks at a reduced learning rate.
- Stratified partitioning with duplicate image detection.
- Balanced class-weighted CrossEntropyLoss.
- Best-model checkpointing tracking validation macro F1.
- Complete per-epoch diagnostic metrics and CSV history tracking.

Usage:
    python -m ml.ear.train `
      --data-dir "C:/final_project/dataset keggle/Dogs ear diseases" `
      --epochs-head 5 `
      --epochs-finetune 15 `
      --batch-size 16 `
      --output-dir model_registry/ear
"""

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ml.ear.dataset import (
    INDEX_TO_LABEL,
    LABELS,
    LABEL_TO_INDEX,
    CanineEarDataset,
    get_eval_transforms,
    get_train_transforms,
    load_labels_csv,
)
from ml.ear.model import build_model, freeze_backbone, unfreeze_top_blocks
from ml.ear.splitting import detect_duplicate_images, stratified_train_val_test_split


def set_seed(seed: int = 42) -> None:
    """Set random seeds across standard library, numpy, and PyTorch for reproducibility."""
    import random
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def compute_metrics(
    y_true: List[int],
    y_pred: List[int],
    num_classes: int = len(LABELS),
) -> Dict[str, object]:
    """Calculate overall accuracy, macro precision/recall/F1, and per-class breakdowns.

    Uses scikit-learn when available; otherwise falls back to a dependency-free
    pure Python computation matching standard macro-averaged definitions.
    """
    if len(y_true) == 0:
        return {
            "accuracy": 0.0,
            "precision_macro": 0.0,
            "recall_macro": 0.0,
            "f1_macro": 0.0,
            "per_class": {INDEX_TO_LABEL.get(i, f"class_{i}"): {"precision": 0.0, "recall": 0.0, "f1": 0.0} for i in range(num_classes)},
        }

    try:
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_recall_fscore_support,
            precision_score,
            recall_score,
        )

        acc = float(accuracy_score(y_true, y_pred))
        p_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        r_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

        per_p, per_r, per_f1, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=list(range(num_classes)), zero_division=0
        )

        per_class = {
            INDEX_TO_LABEL.get(i, f"class_{i}"): {
                "precision": float(per_p[i]),
                "recall": float(per_r[i]),
                "f1": float(per_f1[i]),
            }
            for i in range(num_classes)
        }

        return {
            "accuracy": acc,
            "precision_macro": p_macro,
            "recall_macro": r_macro,
            "f1_macro": f1_macro,
            "per_class": per_class,
        }
    except ImportError:
        # Dependency-free pure Python fallback
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        acc = float(correct / len(y_true))

        precisions, recalls, f1s = [], [], []
        per_class = {}

        for c in range(num_classes):
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)

            label_name = INDEX_TO_LABEL.get(c, f"class_{c}")
            per_class[label_name] = {"precision": float(prec), "recall": float(rec), "f1": float(f1)}

        p_macro = float(sum(precisions) / num_classes)
        r_macro = float(sum(recalls) / num_classes)
        f1_macro = float(sum(f1s) / num_classes)

        return {
            "accuracy": acc,
            "precision_macro": p_macro,
            "recall_macro": r_macro,
            "f1_macro": f1_macro,
            "per_class": per_class,
        }


def evaluate_model(
    model: "torch.nn.Module",
    data_loader: "torch.utils.data.DataLoader",
    criterion: "torch.nn.Module",
    device: "torch.device",
) -> Tuple[float, Dict[str, object]]:
    """Evaluate model on a DataLoader, returning average loss and comprehensive metrics."""
    import torch

    model.eval()
    total_loss = 0.0
    total_batches = 0
    all_preds: List[int] = []
    all_labels: List[int] = []

    with torch.no_grad():
        for images, labels in data_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            total_batches += 1

            preds = outputs.argmax(dim=1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / max(total_batches, 1)
    metrics = compute_metrics(all_labels, all_preds)
    return avg_loss, metrics


def train_pipeline(
    data_dir: str,
    labels_csv: Optional[str] = None,
    epochs_head: int = 5,
    epochs_finetune: int = 15,
    batch_size: int = 16,
    lr_head: float = 1e-3,
    lr_finetune: float = 1e-5,
    seed: int = 42,
    output_dir: str = "model_registry/ear",
    num_workers: int = 0,
) -> Dict[str, object]:
    """Execute the two-stage transfer learning training pipeline.

    Args:
        data_dir: Dataset root directory.
        labels_csv: Path to labels.csv. Defaults to <data_dir>/labels.csv.
        epochs_head: Number of epochs to train only the linear classification head.
        epochs_finetune: Number of epochs to fine-tune top convolutional blocks.
        batch_size: DataLoader batch size.
        lr_head: Initial learning rate for head training.
        lr_finetune: Learning rate for fine-tuning top blocks.
        seed: Random seed for deterministic reproducibility.
        output_dir: Target directory for checkpoints and training history.
        num_workers: DataLoader worker count.

    Returns:
        Summary dictionary with training results and checkpoint paths.
    """
    import torch
    from torch.utils.data import DataLoader

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    data_path = Path(data_dir).resolve()
    csv_path = Path(labels_csv).resolve() if labels_csv else data_path / "labels.csv"

    print("=" * 70)
    print("Canivue Ear - Two-Stage Model Training Pipeline")
    print(f"Device: {device} | Random Seed: {seed}")
    print(f"Dataset: {data_path}")
    print(f"Manifest: {csv_path}")
    print("=" * 70)

    # 1. Load records and detect duplicates
    records = load_labels_csv(csv_path)
    print(f"Loaded {len(records)} total records from manifest.")

    duplicates = detect_duplicate_images(data_path, records)
    if duplicates:
        print(f"[WARNING] Detected {len(duplicates)} sets of identical/duplicate image files:")
        for digest, paths in list(duplicates.items())[:3]:
            print(f"  Hash {digest[:12]}... -> {paths}")
        if len(duplicates) > 3:
            print(f"  ... and {len(duplicates) - 3} more duplicate sets.")
    else:
        print("[CHECK] No duplicate image files detected by byte hash.")

    # 2. Stratified data splitting
    train_records, val_records, test_records = stratified_train_val_test_split(
        records, ratios=(0.70, 0.15, 0.15), seed=seed
    )
    print(f"Stratified Splits: Train={len(train_records)}, Val={len(val_records)}, Test={len(test_records)}")

    # 3. Class weight calculation for imbalanced training set
    class_counts: Dict[int, int] = defaultdict(int)
    for r in train_records:
        class_counts[LABEL_TO_INDEX[r["label"]]] += 1

    total_train = len(train_records)
    num_classes = len(LABELS)
    weights = [
        total_train / (num_classes * max(class_counts[i], 1))
        for i in range(num_classes)
    ]
    weights_tensor = torch.tensor(weights, dtype=torch.float32).to(device)
    print(f"Computed Class Weights for Loss Function: {[round(w, 3) for w in weights]}")

    criterion = torch.nn.CrossEntropyLoss(weight=weights_tensor)

    # 4. DataLoaders
    train_ds = CanineEarDataset(data_path, train_records, transform=get_train_transforms())
    val_ds = CanineEarDataset(data_path, val_records, transform=get_eval_transforms())
    test_ds = CanineEarDataset(data_path, test_records, transform=get_eval_transforms())

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    # 5. Build Model
    model = build_model(num_classes=num_classes, pretrained=True).to(device)

    history_rows: List[Dict[str, object]] = []
    best_val_f1 = -1.0
    total_epochs = epochs_head + epochs_finetune
    current_global_epoch = 0

    # -------------------------------------------------------------
    # STAGE A: Train Classification Head Only (Backbone Frozen)
    # -------------------------------------------------------------
    if epochs_head > 0:
        print("\n" + "-" * 70)
        print(f"STAGE A: Training Classification Head ({epochs_head} epochs, lr={lr_head})")
        print("-" * 70)

        freeze_backbone(model)
        optimizer_head = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=lr_head,
            weight_decay=1e-2,
        )

        for ep in range(1, epochs_head + 1):
            current_global_epoch += 1
            model.train()
            running_loss = 0.0
            batches = 0

            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer_head.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer_head.step()

                running_loss += loss.item()
                batches += 1

            train_loss = running_loss / max(batches, 1)
            val_loss, val_metrics = evaluate_model(model, val_loader, criterion, device)

            val_acc = val_metrics["accuracy"]
            val_prec = val_metrics["precision_macro"]
            val_rec = val_metrics["recall_macro"]
            val_f1 = val_metrics["f1_macro"]

            print(
                f"Epoch {current_global_epoch:02d}/{total_epochs:02d} [Head] | "
                f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                f"Val Acc: {val_acc:.4f} | Val Macro F1: {val_f1:.4f}"
            )

            # Checkpoint best model
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                save_checkpoint(
                    out_path / "model_best.pt",
                    model,
                    optimizer_head,
                    current_global_epoch,
                    "head",
                    val_loss,
                    val_f1,
                    val_metrics,
                    seed,
                )
                print(f"  --> Saved new best checkpoint (Val Macro F1: {best_val_f1:.4f})")

            history_rows.append({
                "epoch": current_global_epoch,
                "stage": "head",
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "val_precision_macro": round(val_prec, 4),
                "val_recall_macro": round(val_rec, 4),
                "val_macro_f1": round(val_f1, 4),
            })

    # -------------------------------------------------------------
    # STAGE B: Fine-Tune Top Convolutional Blocks
    # -------------------------------------------------------------
    if epochs_finetune > 0:
        print("\n" + "-" * 70)
        print(f"STAGE B: Fine-Tuning Top Backbone Blocks ({epochs_finetune} epochs, lr={lr_finetune})")
        print("-" * 70)

        unfreeze_top_blocks(model, num_stages=2)
        optimizer_ft = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=lr_finetune,
            weight_decay=1e-2,
        )

        for ep in range(1, epochs_finetune + 1):
            current_global_epoch += 1
            model.train()
            running_loss = 0.0
            batches = 0

            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)
                optimizer_ft.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer_ft.step()

                running_loss += loss.item()
                batches += 1

            train_loss = running_loss / max(batches, 1)
            val_loss, val_metrics = evaluate_model(model, val_loader, criterion, device)

            val_acc = val_metrics["accuracy"]
            val_prec = val_metrics["precision_macro"]
            val_rec = val_metrics["recall_macro"]
            val_f1 = val_metrics["f1_macro"]

            print(
                f"Epoch {current_global_epoch:02d}/{total_epochs:02d} [FineTune] | "
                f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | "
                f"Val Acc: {val_acc:.4f} | Val Macro F1: {val_f1:.4f}"
            )

            # Checkpoint best model
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                save_checkpoint(
                    out_path / "model_best.pt",
                    model,
                    optimizer_ft,
                    current_global_epoch,
                    "finetune",
                    val_loss,
                    val_f1,
                    val_metrics,
                    seed,
                )
                print(f"  --> Saved new best checkpoint (Val Macro F1: {best_val_f1:.4f})")

            history_rows.append({
                "epoch": current_global_epoch,
                "stage": "finetune",
                "train_loss": round(train_loss, 4),
                "val_loss": round(val_loss, 4),
                "val_accuracy": round(val_acc, 4),
                "val_precision_macro": round(val_prec, 4),
                "val_recall_macro": round(val_rec, 4),
                "val_macro_f1": round(val_f1, 4),
            })

    # Save final model checkpoint
    final_optimizer = optimizer_ft if epochs_finetune > 0 else optimizer_head
    save_checkpoint(
        out_path / "model_final.pt",
        model,
        final_optimizer,
        current_global_epoch,
        "final",
        val_loss,
        val_f1,
        val_metrics,
        seed,
    )
    print(f"\n[DONE] Saved final checkpoint to {out_path / 'model_final.pt'}")

    # Write training history CSV
    history_csv = out_path / "training_history.csv"
    with open(history_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "epoch",
            "stage",
            "train_loss",
            "val_loss",
            "val_accuracy",
            "val_precision_macro",
            "val_recall_macro",
            "val_macro_f1",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history_rows)
    print(f"[DONE] Saved training history to {history_csv}")

    # 6. Post-training evaluation on held-out test split using best model
    best_ckpt_file = out_path / "model_best.pt"
    if best_ckpt_file.exists():
        print("\n" + "=" * 70)
        print("Held-Out Test Split Evaluation (Loading Best Validation Checkpoint)")
        print("=" * 70)
        best_ckpt = torch.load(best_ckpt_file, map_location=device)
        model.load_state_dict(best_ckpt["model_state_dict"])
        test_loss, test_metrics = evaluate_model(model, test_loader, criterion, device)

        print(f"Test Loss: {test_loss:.4f}")
        print(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
        print(f"Test Macro Precision: {test_metrics['precision_macro']:.4f}")
        print(f"Test Macro Recall: {test_metrics['recall_macro']:.4f}")
        print(f"Test Macro F1: {test_metrics['f1_macro']:.4f}")
        print("\nPer-Class Performance on Test Set:")
        for cls_name, p_metrics in test_metrics["per_class"].items():
            print(
                f"  - {cls_name:38s}: Precision={p_metrics['precision']:.4f} "
                f"Recall={p_metrics['recall']:.4f} F1={p_metrics['f1']:.4f}"
            )

    return {
        "best_val_f1": best_val_f1,
        "best_checkpoint": str(out_path / "model_best.pt"),
        "final_checkpoint": str(out_path / "model_final.pt"),
        "history_csv": str(history_csv),
    }


def save_checkpoint(
    path: Path,
    model: "torch.nn.Module",
    optimizer: "torch.optim.Optimizer",
    epoch: int,
    stage: str,
    val_loss: float,
    val_macro_f1: float,
    metrics: Dict[str, object],
    seed: int,
) -> None:
    """Save full metadata checkpoint dictionary."""
    import torch

    checkpoint = {
        "epoch": epoch,
        "stage": stage,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "val_loss": val_loss,
        "val_macro_f1": val_macro_f1,
        "val_accuracy": metrics.get("accuracy", 0.0),
        "val_precision_macro": metrics.get("precision_macro", 0.0),
        "val_recall_macro": metrics.get("recall_macro", 0.0),
        "per_class_metrics": metrics.get("per_class", {}),
        "labels": LABELS,
        "label_to_index": LABEL_TO_INDEX,
        "index_to_label": INDEX_TO_LABEL,
        "architecture": "efficientnet_b0",
        "num_classes": len(LABELS),
        "seed": seed,
    }
    torch.save(checkpoint, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True, help="Directory containing the training images")
    parser.add_argument("--labels-csv", default=None, help="Path to labels.csv (defaults to <data-dir>/labels.csv)")
    parser.add_argument("--epochs-head", type=int, default=5, help="Number of head-only epochs (default: 5)")
    parser.add_argument("--epochs-finetune", type=int, default=15, help="Number of fine-tuning epochs (default: 15)")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16)")
    parser.add_argument("--learning-rate", type=float, default=1e-3, help="Head learning rate (default: 1e-3)")
    parser.add_argument("--finetune-learning-rate", type=float, default=1e-5, help="Finetune learning rate (default: 1e-5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", default="model_registry/ear", help="Directory to save checkpoints and metrics")

    args = parser.parse_args()

    train_pipeline(
        data_dir=args.data_dir,
        labels_csv=args.labels_csv,
        epochs_head=args.epochs_head,
        epochs_finetune=args.epochs_finetune,
        batch_size=args.batch_size,
        lr_head=args.learning_rate,
        lr_finetune=args.finetune_learning_rate,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
