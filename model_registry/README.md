# Model Registry

Versioned, trained model artifacts consumed by the API at inference time
(`app/features/<feature>/infrastructure/ml/engine.py`).

## What goes here

```
model_registry/
├── vision/
│   └── efficientnet_v1.pt        # produced by ml/vision/train.py
├── behavioural/
│   └── cnn_lstm_v1.pt             # produced by ml/behavioural/train.py
└── nlp/
    └── symptom_bert_v1/           # a HuggingFace-style save_pretrained() directory
```

## Why these files are gitignored

Trained weights are large binaries (tens to hundreds of MB) that don't
diff/merge meaningfully in git and bloat clone size fast. `.gitignore`
excludes the weight files themselves (`*.pt`, `*.onnx`, `*.h5`, `*.safetensors`,
checkpoint directories) but keeps this README and the folder structure.

Ship real artifacts one of these ways instead:

- **Cloud storage** (S3/GCS bucket referenced by `MODEL_REGISTRY_DIR` /
  a per-feature `<X>_MODEL_WEIGHTS_PATH` setting in `.env`, downloaded on
  container startup).
- **Git LFS** or **DVC** if the team wants weights versioned alongside code.
- **GitHub Release assets**, pulled down by a setup script for local dev.

## Naming convention

`<modality>/<architecture>_v<n>.<ext>` — bump `<n>` on every retrain that
changes weights, and record the mapping from version string to training run
(dataset snapshot, hyperparameters, eval metrics) in that modality's
`ml/<modality>/README.md`. The serving engine's `model_version` should be
read from the filename stem (see `.agents/skills/ml-feature/SKILL.md`), so
every prediction can be traced back to the exact checkpoint that produced it
-- required for FR-16 (audit and model-version history) in the proposal.
