# Canine Ear Disease Vision Subsystem (`ml/ear`)

Offline training pipeline for the **Canivue Canine Ear Disease Classifier**. It mirrors `ml/vision` (skin) exactly: an `EfficientNet-B0` fine-tuned in two stages to classify canine ear conditions from photographs.

## Module layout

```
ml/ear/
├── dataset.py            # LABELS taxonomy, CanineEarDataset, transforms, labels.csv loader
├── model.py              # EfficientNet-B0 head, freeze_backbone, unfreeze_top_blocks
├── splitting.py          # Class-stratified split + SHA-256 duplicate detection
├── prepare_dataset.py    # Folder scanner, Pillow integrity check, labels.csv generator
├── train.py              # Two-stage training (AdamW, class weights, best-F1 checkpoint)
├── evaluate.py           # Held-out test evaluation (metrics + calibration)
├── verify_pipeline.py    # Standalone sanity-check runner
└── README.md
```

## Class taxonomy

| Index | Class (= dataset folder name) | Meaning |
| :---: | :--- | :--- |
| 0 | `Bacterial_otitis` | Bacterial ear infection |
| 1 | `Ear_mites` | *Otodectes* infestation |
| 2 | `Fungal_otitis` | Yeast / *Malassezia* ear infection |
| 3 | `Healthy` | Normal ear |

> **Set this to match your dataset.** Each label must equal a sub-folder name of the dataset root. If your folders are named differently, edit `LABELS` in `dataset.py` **and** `EXPECTED_CLASSES` in `prepare_dataset.py` (and the list in the tests). Everything else (class count, head size, class weights) adapts automatically.

Expected dataset layout:

```
Dogs ear diseases/
├── Bacterial_otitis/*.jpg
├── Ear_mites/*.jpg
├── Fungal_otitis/*.jpg
└── Healthy/*.jpg
```

## Commands (run from the repo root; PowerShell)

```powershell
pip install -r requirements-ml.txt

# 1. Build labels.csv
python -m ml.ear.prepare_dataset --data-dir "C:\final_project\dataset keggle\Dogs ear diseases"

# 2. Sanity check
python -m ml.ear.verify_pipeline
pytest tests/ml/test_ear_pipeline.py -v

# 3. Train (Stage A head 5 epochs, Stage B fine-tune 15 epochs)
python -m ml.ear.train `
  --data-dir "C:\final_project\dataset keggle\Dogs ear diseases" `
  --labels-csv "C:\final_project\dataset keggle\Dogs ear diseases\labels.csv" `
  --epochs-head 5 --epochs-finetune 15 --batch-size 16 `
  --learning-rate 0.001 --finetune-learning-rate 0.00001 `
  --seed 42 --output-dir model_registry\ear

# 4. Evaluate on the held-out test split (same seed as training)
python -m ml.ear.evaluate `
  --checkpoint model_registry\ear\model_best.pt `
  --data-dir "C:\final_project\dataset keggle\Dogs ear diseases" `
  --labels-csv "C:\final_project\dataset keggle\Dogs ear diseases\labels.csv" `
  --seed 42
```

Outputs in `model_registry/ear/`: `model_best.pt` (best validation macro-F1), `model_final.pt`, `training_history.csv`. Weights are gitignored; see `model_registry/README.md`.

## Methodological note

Splits are stratified at the **image** level (70/15/15). If the dataset has no dog IDs, photos of the same dog can land in different splits, which can inflate test scores. Report this limitation. Ear images may also contain both ears of one dog, so check for near-duplicates.

## Differences from `ml/vision`

- `evaluate.py` uses the same stratified split and seed as `train.py` and loads `model_state_dict` from the checkpoint (the skin `evaluate.py` still uses the older dog-level split and loads a raw state dict, so it won't read checkpoints written by `train.py`).
- `verify_pipeline.py` does not hard-code a dataset size.
