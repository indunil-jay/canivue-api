# ML Engineering Workspace

Offline model training, evaluation, and experimentation for the three
unimodal models described in the proposal (visual, behavioural, NLP). This
is deliberately **separate from `app/`**:

| | `ml/` (this directory) | `app/features/*/infrastructure/ml/` |
|---|---|---|
| Purpose | Train, evaluate, and version models | Serve trained models at request time |
| Runs | Locally / on a GPU box / a notebook, on demand | Inside the FastAPI process, per HTTP request |
| Inputs | Raw datasets, hyperparameters | A single image / sensor window / text string |
| Dependencies | `requirements-ml.txt` (torch, transformers, opencv, pandas, ...) | `requirements.txt` only, unless a real backend is enabled |
| Output | A checkpoint written to `model_registry/<modality>/` | A `Prediction`-shaped DTO returned to a use case |

Keeping them apart means the API can be installed, run, and tested
(`pip install -r requirements.txt && pytest`) without ever pulling in
multi-GB GPU frameworks — those only matter when someone is actively
training or a feature's `<X>_MODEL_BACKEND` setting (see `app/config.py`
and `.agents/skills/ml-feature/SKILL.md`) is switched away from its
default stub engine.

## Layout

```
ml/
├── common/          # Shared, framework-light helpers reused across modalities
│   ├── metrics.py       # accuracy/F1/ROC-AUC/Brier/calibration-error helpers
│   └── data_splitting.py# dog-level train/val/test split (prevents leakage across
│                         # repeated observations of the same dog -- see proposal §5.6)
├── vision/          # EfficientNet-family visual condition classifier
├── behavioural/     # 1D-CNN-LSTM / temporal Transformer over IMU windows
└── nlp/             # Fine-tuned compact BERT/RoBERTa symptom extractor
```

Each modality folder follows the same shape:

```
<modality>/
├── README.md      # dataset location, label schema, current best model_version
├── dataset.py      # PyTorch Dataset / loading & preprocessing for training
├── train.py        # training entrypoint -> writes a checkpoint to model_registry/<modality>/
└── evaluate.py      # computes the metrics from proposal §5.9 against a held-out split
```

## Setup

```bash
pip install -r requirements-ml.txt
```

## Fusion and DPRPE are not here

The Confidence-Weighted Adaptive Fusion Mechanism and the Disease
Progression and Risk Prediction Engine (DPRPE) are **not** deep-learning
models to train offline — they're calculation/orchestration logic (reliability
scoring, weighted combination, risk-factor aggregation) that runs entirely
inside the API. Once built, they belong in `app/features/adaptive_fusion/`
and `app/features/progression_risk/`, following the same clean-architecture
pattern as any other feature — see `.agents/skills/ml-feature/SKILL.md`.
