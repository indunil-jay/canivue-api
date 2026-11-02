# Canine Skin Disease Vision Subsystem (`ml/vision`)

Dedicated offline machine learning pipeline for the **Canivue Canine Skin Disease Classifier**. Fine-tunes an `EfficientNet-B0` convolutional neural network across two training stages to classify canine dermatological conditions from photographs.

---

## 📌 Module Architecture

The `ml/vision/` module is strictly decoupled from the web backend (`app/`):

```
ml/vision/
├── dataset.py            # Taxonomy definitions (LABELS), PyTorch CanineVisionDataset, transforms
├── model.py              # Transfer learning architecture, freeze_backbone, unfreeze_top_blocks
├── splitting.py          # Class-stratified data splitting & duplicate image detection
├── prepare_dataset.py    # Scanner, Pillow integrity validator, labels.csv generator
├── train.py              # Two-stage training pipeline (AdamW, class-weights, best checkpointing)
├── evaluate.py           # Evaluation on held-out test split (metrics & calibration)
├── verify_pipeline.py    # Standalone verification runner for dataset, transforms & training logic
└── README.md             # This technical documentation file
```

---

## 🏷️ Class Taxonomy & Mappings

The model classifies 4 mutually exclusive skin conditions:

| Integer Index | Condition Class Name | Clinical Manifestation |
| :---: | :--- | :--- |
| **`0`** | `Bacterial_dermatosis` | Superficial/deep pyoderma, bacterial folliculitis, epidermal collarettes |
| **`1`** | `Fungal_infections` | Dermatophytosis (ringworm), *Malassezia* dermatitis, scaling, crusting |
| **`2`** | `Healthy` | Normal canine skin surface, intact barrier, healthy hair follicles |
| **`3`** | `Hypersensitivity_allergic_dermatosis` | Atopic dermatitis, flea allergy dermatitis, contact hypersensitivity, erythema |

These mappings are defined in [`ml/vision/dataset.py`](dataset.py):
```python
LABELS: List[str] = [
    "Bacterial_dermatosis",
    "Fungal_infections",
    "Healthy",
    "Hypersensitivity_allergic_dermatosis",
]
LABEL_TO_INDEX: Dict[str, int] = {label: i for i, label in enumerate(LABELS)}
INDEX_TO_LABEL: Dict[int, str] = {i: label for i, label in enumerate(LABELS)}
```

---

## 🛠️ Component Breakdown

### 1. Dataset Preparation (`prepare_dataset.py`)
- **Purpose:** Scans the raw Kaggle dataset directory, checks each file extension (`.jpg`, `.jpeg`, `.png`, `.webp`), performs deep raster decoding with Pillow (`img.verify()` and `img.load()`), and generates a clean `labels.csv`.
- **Subject-Level Fallback ID:** Because the Kaggle dataset does not track individual dog IDs, the script assigns transparent fallback identifiers (`img_fallback_<class>_<idx:04d>`).
- **Safety:** Ignores non-image artifacts (e.g., `desktop.ini`, `.DS_Store`) and logs any corrupted files without stopping execution.

### 2. Stratified Data Splitting & Duplicate Detection (`splitting.py`)
- **`stratified_train_val_test_split()`:** Partitions the records into train (70%), validation (15%), and test (15%) splits while preserving exact class proportions. Guarantees zero path overlap across sets (`train ∩ val = ∅`, `train ∩ test = ∅`, `val ∩ test = ∅`).
- **`detect_duplicate_images()`:** Computes SHA-256 byte hashes for all candidate images to identify identical images across class folders prior to partitioning.
- **Methodological Limitation:** The Kaggle dataset lacks dog-level IDs; splits are stratified at the image level. It does not prevent subject-level leakage if multiple photos of the same dog exist. Test data is strictly sequestered from training.

### 3. Dataset Loading & Transforms (`dataset.py`)
- **`CanineVisionDataset`:** Subclasses PyTorch's `Dataset`. Reads records from `labels.csv`, resolves images relative to `data_dir`, opens images in RGB mode, applies transforms, and returns `(tensor, label_idx)`.
- **Strict Error Handling:** Raises `FileNotFoundError` if an image is missing and `ValueError` if a label is unrecognized. Does not drop bad data silently.
- **Transform Separation:**
  - **Training (`get_train_transforms`):** Resize to `224x224`, `RandomHorizontalFlip(p=0.5)`, `ColorJitter(brightness=0.2, contrast=0.2)`, `ToTensor()`, ImageNet normalization.
  - **Evaluation (`get_eval_transforms`):** Deterministic resize to `224x224`, `ToTensor()`, ImageNet normalization. Zero random noise ensures repeatable benchmarking.

### 4. Neural Network Architecture (`model.py`)
- **Backbone:** `torchvision.models.efficientnet_b0(weights="IMAGENET1K_V1")`.
- **Classification Head:** Replaces `model.classifier[1]` with `torch.nn.Linear(in_features=1280, out_features=4)`.
- **Freezing Utilities:**
  - `freeze_backbone(model)`: Freezes all `model.features` stages; only `model.classifier` is trainable.
  - `unfreeze_top_blocks(model, num_stages=2)`: Unfreezes stages 7 and 8 while keeping stages 0–6 frozen.

### 5. Two-Stage Training Pipeline (`train.py`)
- **Stage A (Head Training):** Trains the classification head for `--epochs-head` (default 5) with frozen backbone at `--learning-rate 0.001`.
- **Stage B (Fine-Tuning):** Unfreezes top convolutional stages for `--epochs-finetune` (default 15) at a gentle `--finetune-learning-rate 0.00001`.
- **Optimizer:** `AdamW(weight_decay=0.01)`.
- **Class-Weighted Loss:** Computes inverse-frequency class weights from the training split and injects them into `torch.nn.CrossEntropyLoss` to counteract class imbalance.
- **Checkpointing (`save_checkpoint`):**
  - Evaluates validation macro F1 after every epoch.
  - Saves `model_best.pt` **only when validation macro F1 improves**.
  - Saves `model_final.pt` upon training completion.
  - Writes per-epoch telemetry to `training_history.csv`.
- **Held-Out Test Set Evaluation:** Evaluates `model_best.pt` against the sequestered test split at the conclusion of training.

---

## 💾 Checkpoint Artifact Structure

Saved checkpoints (`model_best.pt`, `model_final.pt`) contain full diagnostic metadata:

```python
{
    "epoch": int,
    "stage": str,                      # 'head' or 'finetune'
    "model_state_dict": OrderedDict,
    "optimizer_state_dict": dict,
    "val_loss": float,
    "val_macro_f1": float,
    "val_accuracy": float,
    "val_precision_macro": float,
    "val_recall_macro": float,
    "per_class_metrics": dict,         # Precision, recall, F1 per class
    "labels": list,                    # Exact 4-class taxonomy
    "label_to_index": dict,
    "index_to_label": dict,
    "architecture": "efficientnet_b0",
    "num_classes": 4,
    "seed": int,
}
```

---

## 💻 PowerShell Command Reference (Windows)

All commands should be executed from the **repository root** (`C:\final_project\my dev\vision AI\canivue-api`):

### 1. Generate Dataset Manifest
```powershell
python -m ml.vision.prepare_dataset `
  --data-dir "C:\final_project\dataset keggle\Dogs skin diseses"
```

### 2. Verify Pipeline Sanity
```powershell
python -m ml.vision.verify_pipeline
```

### 3. Run Automated Tests
```powershell
# Using direct test runner:
python tests/ml/test_vision_pipeline.py

# Or using pytest (if installed):
pytest tests/ml/test_vision_pipeline.py -v
```

### 4. Train Model (Two-Stage Transfer Learning)
```powershell
python -m ml.vision.train `
  --data-dir "C:\final_project\dataset keggle\Dogs skin diseses" `
  --labels-csv "C:\final_project\dataset keggle\Dogs skin diseses\labels.csv" `
  --epochs-head 5 `
  --epochs-finetune 15 `
  --batch-size 16 `
  --learning-rate 0.001 `
  --finetune-learning-rate 0.00001 `
  --seed 42 `
  --output-dir model_registry\vision
```

### 5. Evaluate Checkpoint
```powershell
python -m ml.vision.evaluate `
  --checkpoint model_registry\vision\model_best.pt `
  --data-dir "C:\final_project\dataset keggle\Dogs skin diseses" `
  --labels-csv "C:\final_project\dataset keggle\Dogs skin diseses\labels.csv"
```

---

## 🔧 Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'PIL'` | Pillow is not installed in the active environment. | Run `pip install Pillow` or `pip install -r requirements-ml.txt`. |
| `ModuleNotFoundError: No module named 'torch'` | PyTorch is missing. | Install PyTorch via `pip install -r requirements-ml.txt` or visit [pytorch.org](https://pytorch.org) for your CUDA version. |
| `FileNotFoundError: [Errno 2] No such file...` | Path containing spaces was not enclosed in quotes in PowerShell. | Always wrap file paths in double quotes: `"C:\final_project\dataset keggle\Dogs skin diseses"`. |
| `PermissionError: [Errno 13] Permission denied` | Output directory lacks write permissions or destination file is locked. | Ensure the target directory exists and is writable, or run PowerShell as Administrator if restricted. |
| `CUDA out of memory` | Batch size is too large for the available GPU VRAM. | Reduce `--batch-size` to `16` or `8` in the `train.py` command. |
