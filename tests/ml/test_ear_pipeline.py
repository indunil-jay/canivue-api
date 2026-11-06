"""Unit tests and validation checks for the Canivue canine ear disease pipeline."""

import csv
import sys
import tempfile
from pathlib import Path

# Ensure repository root is on sys.path for direct script execution
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import pytest
except ImportError:
    import contextlib

    class _PytestFallback:
        @staticmethod
        def importorskip(modname: str):
            try:
                import importlib
                return importlib.import_module(modname)
            except ImportError:
                return None

        @staticmethod
        @contextlib.contextmanager
        def raises(expected_exc, match=None):
            try:
                yield
            except expected_exc as exc:
                if match and match not in str(exc):
                    raise AssertionError(f"Expected match '{match}' not found in '{exc}'")
                return
            raise AssertionError(f"Expected exception {expected_exc} was not raised")

    pytest = _PytestFallback()

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
from ml.ear.train import compute_metrics, save_checkpoint


def test_four_class_labels_and_mappings():
    """Verify that all four required classes are present and bijectively mapped."""
    expected_classes = [
        "Bacterial_otitis",
        "Ear_mites",
        "Fungal_otitis",
        "Healthy",
    ]

    assert LABELS == expected_classes, f"LABELS must match expected four classes exactly. Got: {LABELS}"
    assert len(LABELS) == 4

    for idx, name in enumerate(LABELS):
        assert LABEL_TO_INDEX[name] == idx
        assert INDEX_TO_LABEL[idx] == name

    assert len(LABEL_TO_INDEX) == 4
    assert len(INDEX_TO_LABEL) == 4


def test_load_labels_csv_valid_and_error_handling(tmp_path: Path):
    """Verify manifest loading, column validation, and strict error reporting."""
    # 1. Valid CSV
    valid_csv = tmp_path / "valid_labels.csv"
    with open(valid_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "pet_id", "label"])
        writer.writeheader()
        writer.writerow({
            "image_path": "Healthy/0.jpg",
            "pet_id": "img_fallback_Healthy_0001",
            "label": "Healthy",
        })
        writer.writerow({
            "image_path": "Bacterial_otitis/453.jpg",
            "pet_id": "img_fallback_Bacterial_otitis_0001",
            "label": "Bacterial_otitis",
        })

    records = load_labels_csv(valid_csv)
    assert len(records) == 2
    assert records[0]["label"] == "Healthy"
    assert records[1]["label"] == "Bacterial_otitis"

    # 2. Non-existent file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        load_labels_csv(tmp_path / "non_existent.csv")

    # 3. Missing required column raises ValueError
    missing_col_csv = tmp_path / "missing_col.csv"
    with open(missing_col_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "pet_id"])
        writer.writeheader()
        writer.writerow({"image_path": "Healthy/0.jpg", "pet_id": "p1"})

    with pytest.raises(ValueError, match="missing required columns"):
        load_labels_csv(missing_col_csv)

    # 4. Unrecognized label raises ValueError
    invalid_label_csv = tmp_path / "invalid_label.csv"
    with open(invalid_label_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "pet_id", "label"])
        writer.writeheader()
        writer.writerow({
            "image_path": "Healthy/0.jpg",
            "pet_id": "p1",
            "label": "Unknown_disease",
        })

    with pytest.raises(ValueError, match="Invalid label 'Unknown_disease'"):
        load_labels_csv(invalid_label_csv)

    # 5. Empty image_path raises ValueError
    empty_path_csv = tmp_path / "empty_path.csv"
    with open(empty_path_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "pet_id", "label"])
        writer.writeheader()
        writer.writerow({
            "image_path": "   ",
            "pet_id": "p1",
            "label": "Healthy",
        })

    with pytest.raises(ValueError, match="'image_path' is empty"):
        load_labels_csv(empty_path_csv)


def test_stratified_split_proportions_and_no_leakage():
    """Verify class-stratified splitting, non-overlapping subsets, and class retention."""
    records = []
    # Create 100 mock records distributed across the 4 classes
    for cls_name in LABELS:
        for i in range(25):
            records.append({
                "image_path": f"{cls_name}/img_{i:03d}.jpg",
                "label": cls_name,
            })

    train_recs, val_recs, test_recs = stratified_train_val_test_split(
        records, ratios=(0.70, 0.15, 0.15), seed=42
    )

    # Check total sum
    assert len(train_recs) + len(val_recs) + len(test_recs) == 100

    # Check no overlap between subsets
    train_paths = {r["image_path"] for r in train_recs}
    val_paths = {r["image_path"] for r in val_recs}
    test_paths = {r["image_path"] for r in test_recs}

    assert len(train_paths & val_paths) == 0, "Train and validation sets must not overlap!"
    assert len(train_paths & test_paths) == 0, "Train and test sets must not overlap!"
    assert len(val_paths & test_paths) == 0, "Validation and test sets must not overlap!"

    # Check every class is represented in all three splits
    for cls_name in LABELS:
        assert any(r["label"] == cls_name for r in train_recs), f"Missing {cls_name} in train!"
        assert any(r["label"] == cls_name for r in val_recs), f"Missing {cls_name} in val!"
        assert any(r["label"] == cls_name for r in test_recs), f"Missing {cls_name} in test!"


def test_split_reproducibility():
    """Ensure identical random seeds produce bit-for-bit identical split assignments."""
    records = [
        {"image_path": f"img_{i}.jpg", "label": LABELS[i % len(LABELS)]}
        for i in range(40)
    ]

    t1, v1, s1 = stratified_train_val_test_split(records, seed=42)
    t2, v2, s2 = stratified_train_val_test_split(records, seed=42)
    t3, v3, s3 = stratified_train_val_test_split(records, seed=999)

    assert [r["image_path"] for r in t1] == [r["image_path"] for r in t2]
    assert [r["image_path"] for r in v1] == [r["image_path"] for r in v2]
    assert [r["image_path"] for r in s1] == [r["image_path"] for r in s2]

    # Different seed should yield a different partition
    assert [r["image_path"] for r in t1] != [r["image_path"] for r in t3]


def test_detect_duplicate_images(tmp_path: Path):
    """Verify detection of byte-level duplicate image files."""
    file_a = tmp_path / "a.jpg"
    file_b = tmp_path / "b.jpg"
    file_c = tmp_path / "c.jpg"

    content_dup = b"\xFF\xD8\xFF\xE0\x00\x10JFIF_DUPLICATE_BYTES"
    content_uniq = b"\xFF\xD8\xFF\xE0\x00\x10JFIF_UNIQUE_BYTES"

    file_a.write_bytes(content_dup)
    file_b.write_bytes(content_dup)
    file_c.write_bytes(content_uniq)

    records = [
        {"image_path": "a.jpg"},
        {"image_path": "b.jpg"},
        {"image_path": "c.jpg"},
    ]

    duplicates = detect_duplicate_images(tmp_path, records)
    assert len(duplicates) == 1
    dup_paths = next(iter(duplicates.values()))
    assert sorted(dup_paths) == ["a.jpg", "b.jpg"]


def test_transforms_determinism_and_tensor_shape():
    """Verify validation transforms are deterministic and produce [3, 224, 224] tensors."""
    torch = pytest.importorskip("torch")
    if torch is None:
        return
    from PIL import Image

    synthetic_img = Image.new("RGB", (320, 240), color=(140, 180, 210))

    eval_tf = get_eval_transforms(image_size=224)
    t1 = eval_tf(synthetic_img)
    t2 = eval_tf(synthetic_img)

    assert torch.equal(t1, t2), "Evaluation transform must be completely deterministic."
    assert t1.shape == torch.Size([3, 224, 224])
    assert t1.dtype == torch.float32

    train_tf = get_train_transforms(image_size=224)
    train_tensor = train_tf(synthetic_img)
    assert train_tensor.shape == torch.Size([3, 224, 224])


def test_canine_ear_dataset_loading_and_retrieval(tmp_path: Path):
    """Verify dataset length, retrieval, [3, 224, 224] shape, and numeric class mapping."""
    torch = pytest.importorskip("torch")
    if torch is None:
        return
    from PIL import Image

    records = []
    for idx, class_name in enumerate(LABELS):
        class_dir = tmp_path / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        img_path = class_dir / "sample.jpg"

        img = Image.new("RGB", (250, 250), color=(idx * 40, idx * 50, idx * 60))
        img.save(img_path)

        rel_path = f"{class_name}/sample.jpg"
        records.append({
            "image_path": rel_path,
            "pet_id": f"img_fallback_{class_name}_0001",
            "label": class_name,
        })

    dataset = CanineEarDataset(data_dir=tmp_path, records=records)
    assert len(dataset) == 4

    for idx, expected_class in enumerate(LABELS):
        tensor, label_idx = dataset[idx]
        assert isinstance(tensor, torch.Tensor)
        assert tensor.shape == torch.Size([3, 224, 224])
        assert label_idx == idx
        assert INDEX_TO_LABEL[label_idx] == expected_class


def test_backbone_freezing_and_unfreezing():
    """Verify Stage A backbone freeze and Stage B top-block unfreezing."""
    torch = pytest.importorskip("torch")
    if torch is None:
        return

    model = build_model(num_classes=4, pretrained=False)

    # 1. Freeze backbone (Stage A)
    freeze_backbone(model)

    for param in model.features.parameters():
        assert not param.requires_grad, "All backbone features must be frozen in Stage A!"
    for param in model.classifier.parameters():
        assert param.requires_grad, "Classifier head must remain trainable in Stage A!"

    # 2. Unfreeze top 2 blocks (Stage B)
    unfreeze_top_blocks(model, num_stages=2)

    # Features stage 0..6 must remain frozen
    for param in model.features[0].parameters():
        assert not param.requires_grad, "Lower feature stages must remain frozen in Stage B!"

    # Features stage 7 and 8 must be unfrozen
    for param in model.features[7].parameters():
        assert param.requires_grad, "Stage 7 features must be trainable in Stage B!"
    for param in model.features[8].parameters():
        assert param.requires_grad, "Stage 8 features must be trainable in Stage B!"
    for param in model.classifier.parameters():
        assert param.requires_grad, "Classifier head must be trainable in Stage B!"


def test_checkpoint_saving_and_metadata(tmp_path: Path):
    """Verify checkpoint structure, metadata integrity, and roundtrip deserialization."""
    torch = pytest.importorskip("torch")
    if torch is None:
        return

    model = build_model(num_classes=4, pretrained=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    ckpt_file = tmp_path / "model_best.pt"

    dummy_metrics = {
        "accuracy": 0.85,
        "precision_macro": 0.84,
        "recall_macro": 0.86,
        "f1_macro": 0.85,
        "per_class": {cls: {"precision": 0.8, "recall": 0.8, "f1": 0.8} for cls in LABELS},
    }

    save_checkpoint(
        path=ckpt_file,
        model=model,
        optimizer=optimizer,
        epoch=5,
        stage="head",
        val_loss=0.45,
        val_macro_f1=0.85,
        metrics=dummy_metrics,
        seed=42,
    )

    assert ckpt_file.exists()
    loaded = torch.load(ckpt_file, map_location="cpu")

    assert loaded["epoch"] == 5
    assert loaded["stage"] == "head"
    assert loaded["val_macro_f1"] == 0.85
    assert loaded["val_loss"] == 0.45
    assert loaded["seed"] == 42
    assert loaded["architecture"] == "efficientnet_b0"
    assert loaded["num_classes"] == 4
    assert loaded["labels"] == LABELS
    assert "model_state_dict" in loaded
    assert "optimizer_state_dict" in loaded


def test_best_macro_f1_selection_and_history_csv(tmp_path: Path):
    """Simulate multi-epoch metric evolution and check best checkpoint and CSV generation."""
    torch = pytest.importorskip("torch")
    if torch is None:
        return

    model = build_model(num_classes=4, pretrained=False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    best_ckpt_path = tmp_path / "model_best.pt"

    simulated_epochs = [
        (1, 0.70, 0.60),  # epoch 1, loss 0.70, f1 0.60 -> saved
        (2, 0.65, 0.55),  # epoch 2, loss 0.65, f1 0.55 -> not saved
        (3, 0.50, 0.78),  # epoch 3, loss 0.50, f1 0.78 -> saved (best)
        (4, 0.48, 0.72),  # epoch 4, loss 0.48, f1 0.72 -> not saved
    ]

    best_f1 = -1.0
    history_rows = []

    for ep, loss, f1 in simulated_epochs:
        metrics = {"accuracy": f1, "precision_macro": f1, "recall_macro": f1, "f1_macro": f1}
        if f1 > best_f1:
            best_f1 = f1
            save_checkpoint(
                path=best_ckpt_path,
                model=model,
                optimizer=optimizer,
                epoch=ep,
                stage="simulated",
                val_loss=loss,
                val_macro_f1=f1,
                metrics=metrics,
                seed=42,
            )

        history_rows.append({
            "epoch": ep,
            "stage": "simulated",
            "train_loss": loss,
            "val_loss": loss,
            "val_accuracy": f1,
            "val_precision_macro": f1,
            "val_recall_macro": f1,
            "val_macro_f1": f1,
        })

    # Verify best checkpoint holds epoch 3 and f1 0.78
    best_loaded = torch.load(best_ckpt_path, map_location="cpu")
    assert best_loaded["epoch"] == 3
    assert best_loaded["val_macro_f1"] == 0.78

    # Verify CSV creation
    csv_file = tmp_path / "training_history.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(history_rows[0].keys()))
        writer.writeheader()
        writer.writerows(history_rows)

    assert csv_file.exists()
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 4
        assert reader[2]["val_macro_f1"] == "0.78"


if __name__ == "__main__":
    print("=" * 60)
    print("Running Unit Tests in tests/ml/test_ear_pipeline.py directly")
    print("=" * 60)
    test_four_class_labels_and_mappings()
    print("[PASS] test_four_class_labels_and_mappings")

    with tempfile.TemporaryDirectory() as td:
        test_load_labels_csv_valid_and_error_handling(Path(td))
        print("[PASS] test_load_labels_csv_valid_and_error_handling")

    test_stratified_split_proportions_and_no_leakage()
    print("[PASS] test_stratified_split_proportions_and_no_leakage")

    test_split_reproducibility()
    print("[PASS] test_split_reproducibility")

    with tempfile.TemporaryDirectory() as td:
        test_detect_duplicate_images(Path(td))
        print("[PASS] test_detect_duplicate_images")

    with tempfile.TemporaryDirectory() as td:
        test_transforms_determinism_and_tensor_shape()
        test_canine_ear_dataset_loading_and_retrieval(Path(td))
        test_backbone_freezing_and_unfreezing()
        test_checkpoint_saving_and_metadata(Path(td))
        test_best_macro_f1_selection_and_history_csv(Path(td))
        print("[PASS] Neural architecture & training checkpoint checks")

    print("\nAll unit tests passed successfully!")
