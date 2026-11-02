# Canivue: AI-Powered Canine Health Monitoring System

> **Diagnostic AI Subsystem: Canine Skin Disease Classification**  
> *A modular, production-ready AI and backend architecture built with FastAPI, PyTorch, and Feature-Based Clean Architecture.*

---

## 📋 Table of Contents

- [Overview & Objectives](#-overview--objectives)
- [System Architecture](#-system-architecture)
- [Technologies & Frameworks](#-technologies--frameworks)
- [Dataset Specifications](#-dataset-specifications)
- [AI Model Development Workflow](#-ai-model-development-workflow)
- [Installation & Environment Setup](#-installation--environment-setup)
- [Step-by-Step Execution Guide](#-step-by-step-execution-guide)
  - [1. Dataset Manifest Generation](#1-dataset-manifest-generation)
  - [2. Pipeline Verification](#2-pipeline-verification)
  - [3. Running Unit Tests](#3-running-unit-tests)
  - [4. Model Training](#4-model-training)
  - [5. Model Evaluation](#5-model-evaluation)
- [Model Checkpoints & Registry](#-model-checkpoints--registry)
- [Development Roadmap & Phase Tracking](#-development-roadmap--phase-tracking)
- [Known Limitations & Future Work](#-known-limitations--future-work)
- [Clinical & Veterinary Disclaimer](#-clinical--veterinary-disclaimer)

---

## 🎯 Overview & Objectives

**Canivue** is an intelligent veterinary health-monitoring platform designed to assist dog owners and veterinary professionals in early triage, screening, and condition tracking. 

The **Skin Disease Classification Subsystem** provides automated visual classification of common canine dermatological conditions from photographs, enabling:
- **Early Detection:** Identifying potential bacterial, fungal, or hypersensitivity-related skin conditions before they worsen.
- **Triage Assistance:** Assisting pet owners in determining when a prompt clinic visit is warranted.
- **Objective Baseline:** Providing visual condition classification paired with confidence scores and future explainability heatmaps (Grad-CAM).

---

## 🏛️ System Architecture

Canivue separates **Offline AI/ML Engineering** from **Online API Serving** via Feature-Based Clean Architecture inside a Modular Monolith.

```
canivue-api/
│
├── ml/                                 # 🧪 OFFLINE ML WORKBENCH (Zero backend coupling)
│   ├── common/                         # Shared data splitting & clinical metrics
│   │   ├── data_splitting.py           # Subject-level salted hash train/val/test splitting
│   │   └── metrics.py                  # Macro metrics, ECE calibration, Brier score
│   ├── vision/                         # 👁️ CANINE SKIN DISEASE CLASSIFIER
│   │   ├── dataset.py                  # PyTorch Dataset & deterministic/augmented transforms
│   │   ├── model.py                    # EfficientNet-B0 backbone with custom 4-class head
│   │   ├── prepare_dataset.py          # Manifest generator & deep Pillow integrity scanner
│   │   ├── train.py                    # Training entrypoint & optimization loop
│   │   ├── evaluate.py                 # Evaluation against held-out test split
│   │   ├── verify_pipeline.py          # Standalone verification runner
│   │   └── README.md                   # Dedicated vision subsystem documentation
│   ├── behavioural/                    # 🐕 Sensor / behavioural 1D-CNN skeleton
│   └── nlp/                            # 📝 Symptom extraction NLP skeleton
│
├── model_registry/                     # 💾 VERSIONED MODEL ARTIFACTS (Gitignored binaries)
│   └── vision/                         # Target location for trained .pt / .onnx checkpoints
│
├── app/                                # 🌐 FASTAPI APPLICATION (Production Web Service)
│   ├── core/                           # Database, security, exceptions, logging middleware
│   ├── shared/                         # Base entities & repository interfaces
│   └── features/                       # Encapsulated feature slices
│       ├── auth/                       # Authentication, tokens, RBAC
│       ├── symptom_nlp/                # NLP symptom extraction feature
│       └── (vision_diagnosis/)         # Future online serving feature (Protocol + Stub/Trained)
│
└── tests/                              # 🧪 AUTOMATED TESTS
    ├── features/                       # Integration & API tests
    └── ml/                             # Offline pipeline unit tests
        └── test_vision_pipeline.py     # Vision dataset, transform, and model unit tests
```

---

## ⚙️ Technologies & Frameworks

| Domain | Technology / Library | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Deep Learning** | `PyTorch` | `>= 2.2.0` | Core tensor computation, neural network training |
| **Vision Backbone** | `Torchvision` | `>= 0.17.0` | Pretrained EfficientNet-B0 weights, image transforms |
| **Image Processing** | `Pillow` (PIL) | `>= 10.0.0` | File decoding, raster validation |
| **Computer Vision** | `OpenCV Headless` | `>= 4.9.0` | Visual explainability & Grad-CAM heatmaps |
| **Metrics & Calibration**| `scikit-learn` / `scipy` | `>= 1.4.0` | Precision/Recall/F1, Expected Calibration Error (ECE) |
| **Data Handling** | `pandas` / `numpy` | `>= 2.2.0` | CSV manipulation, array operations |
| **Serving Runtime** | `FastAPI` / `Uvicorn` | `>= 0.110.0` | Asynchronous REST API serving |
| **Testing** | `pytest` / `pytest-asyncio` | `>= 8.1.0` | Automated test suite execution |

---

## 📦 Dataset Specifications

The model is configured for the **Kaggle Dogs Skin Diseases** dataset:

* **Location:** `C:\final_project\dataset keggle\Dogs skin diseses`
* **Generated Manifest:** `C:\final_project\dataset keggle\Dogs skin diseses\labels.csv`
* **Total Valid Images:** `442` (plus 1 ignored `.ini` file)

### Class Distribution

| Index | Condition Class | Image Count | Description |
| :---: | :--- | :---: | :--- |
| `0` | `Bacterial_dermatosis` | 97 | Bacterial infections, pyoderma, folliculitis |
| `1` | `Fungal_infections` | 137 | Ringworm, yeast dermatitis (*Malassezia*) |
| `2` | `Healthy` | 119 | Normal skin, coat, and epithelial tissue |
| `3` | `Hypersensitivity_allergic_dermatosis` | 89 | Atopic dermatitis, flea allergy, contact allergies |
| — | **Total** | **442** | Verified JPG, JPEG, PNG, and WEBP images |

---

## 🔄 AI Model Development Workflow

```
[Raw Class Folders]
       │
       ▼
[ml.vision.prepare_dataset] ──> Pillow Verification & Filter ──> [labels.csv Manifest]
                                                                        │
       ┌────────────────────────────────────────────────────────────────┘
       ▼
[ml.vision.dataset.CanineVisionDataset]
       │
       ├──> Training Split (70%)   ──> get_train_transforms() (Augmented) ──> [train.py]
       │                                                                          │
       ├──> Validation Split (15%) ──> get_eval_transforms()  (Deterministic) ─┐  │
       │                                                                       ▼  ▼
       └──> Test Split (15%)       ──> get_eval_transforms()  (Deterministic) ──> [evaluate.py]
                                                                                   │
                                                                                   ▼
                                                                     [model_registry/vision/]
                                                                       efficientnet_v1.pt
```

---

## 💻 Installation & Environment Setup

### 1. Prerequisites (Windows PowerShell)

Ensure Python 3.10+ is available on your machine.

```powershell
# Verify Python version
python --version
```

### 2. Create and Activate Virtual Environment

```powershell
# Navigate to the repository root
cd "C:\final_project\my dev\vision AI\canivue-api"

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

* **Lightweight API & Development (Zero GPU / Zero Torch):**
  ```powershell
  pip install -r requirements.txt
  ```

* **Offline ML & Vision Training (Full ML Suite):**
  ```powershell
  pip install -r requirements-ml.txt
  ```

---

## 🚀 Step-by-Step Execution Guide

### 1. Dataset Manifest Generation

Scans the 4 class folders, validates image integrity, removes non-image files, and outputs `labels.csv` directly in the dataset folder:

```powershell
python -m ml.vision.prepare_dataset --data-dir "C:\final_project\dataset keggle\Dogs skin diseses"
```

### 2. Pipeline Verification

Run the built-in verification script to validate taxonomy mappings, manifest integrity, and deterministic transforms:

```powershell
python -m ml.vision.verify_pipeline
```

### 3. Running Unit Tests

Run the automated test suite with `pytest`:

```powershell
pytest tests/ml/test_vision_pipeline.py -v
```

### 4. Model Training (Two-Stage Transfer Learning)

Executes two-stage transfer learning (Stage A: train classification head with frozen backbone; Stage B: fine-tune top convolutional blocks at `1e-5`):

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

Artifacts produced in `model_registry\vision\`:
- `model_best.pt`: Checkpoint with highest validation macro F1 score.
- `model_final.pt`: Final checkpoint after completing all epochs.
- `training_history.csv`: Per-epoch metrics log (loss, accuracy, macro precision, recall, F1).

### 5. Model Evaluation

Evaluates the best checkpoint on the held-out test split, reporting accuracy, precision, recall, F1, and Expected Calibration Error (ECE):

```powershell
python -m ml.vision.evaluate `
  --checkpoint model_registry\vision\model_best.pt `
  --data-dir "C:\final_project\dataset keggle\Dogs skin diseses" `
  --labels-csv "C:\final_project\dataset keggle\Dogs skin diseses\labels.csv"
```

---

## 💾 Model Checkpoints & Registry

Trained weights and metadata are saved in [`model_registry/vision/`](model_registry/vision/):
* `model_best.pt`: Model state dictionary, optimizer state, epoch, validation loss, validation macro F1, and class mappings corresponding to the peak validation macro F1.
* `model_final.pt`: Final epoch state dictionary and optimization state.
* `training_history.csv`: Tabular progression log tracking loss and macro metrics per epoch.
* Binary model checkpoints (`*.pt`, `*.onnx`) are gitignored to maintain a clean repository.

---

## 🗺️ Development Roadmap & Phase Tracking

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **Phase 1** | **Dataset Manifest Generation** | `prepare_dataset.py` scanner, non-image filtering, Pillow integrity verification, synthetic fallback ID generation, manifest output outside git repo. | **Completed** |
| **Phase 2** | **Dataset Loader & Architecture** | 4-class taxonomy definition in `dataset.py`, decoupled train/eval transforms, `model.py` EfficientNet-B0 builder, unit test suite in `tests/ml/test_vision_pipeline.py`. | **Completed & Verified** |
| **Phase 3** | **Model Training & Checkpointing** | Two-stage transfer learning in `train.py` (Stage A: head training; Stage B: top-block fine-tuning), stratified train/val/test splitting in `splitting.py`, duplicate image detection, class-weighted CrossEntropyLoss, best validation macro F1 checkpointing (`model_best.pt`), and `training_history.csv`. | **Completed & Verified** |
| **Phase 4** | **Evaluation & Calibration** | Comprehensive test-set evaluation, confusion matrix generation, temperature scaling calibration for confidence reliability. | **Pending** |
| **Phase 5** | **Export & API Serving** | ONNX export target, Grad-CAM visual explainability heatmap generator, FastAPI Clean Architecture feature `app/features/vision_diagnosis/`. | **Pending** |
| **Phase 6** | **Flutter App Integration** | Camera capture flow, image upload to `/api/v1/vision/diagnose`, diagnosis visualization card with Grad-CAM overlay. | **Pending** |
| **Phase 5** | **Export & API Serving** | ONNX export target, Grad-CAM visual explainability heatmap generator, FastAPI Clean Architecture feature `app/features/vision_diagnosis/`. | **Pending** |
| **Phase 6** | **Flutter App Integration** | Camera capture flow, image upload to `/api/v1/vision/diagnose`, diagnosis visualization card with Grad-CAM overlay. | **Pending** |

---

## ⚠️ Known Limitations & Future Work

1. **Small Dataset Size (442 images):**  
   With approximately 89 to 137 images per class, the model is susceptible to overfitting. Strict regularization (mild color jitter, horizontal flips, dropout, and early stopping) is essential during Phase 3 training.
2. **Synthetic Subject Identifiers:**  
   The Kaggle dataset lacks patient/dog-level identifiers. The pipeline generates deterministic fallback IDs (`img_fallback_<class>_<idx>`), treating each image as an independent dog. Future iterations will incorporate clinical multi-image dog datasets.
3. **Lighting & Fur Occlusion:**  
   Photos taken under varied smartphone lighting conditions or with dense, unclipped canine fur can obscure dermal lesions. Quality validation checks should be added during Phase 5 serving.

---

## 🩺 Clinical & Veterinary Disclaimer

> **IMPORTANT NOTICE:**  
> The Canivue AI Skin Disease Classification model is designed strictly as an **assistive screening and educational triage tool**. It does **not** provide definitive veterinary medical diagnoses, replace clinical examinations, or substitute for laboratory cytology, skin scrapings, fungal cultures, or biopsies conducted by a licensed veterinary practitioner. Always consult a veterinarian for canine health decisions.
