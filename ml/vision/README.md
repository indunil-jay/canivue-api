# Vision Model

Fine-tunes an EfficientNet-family CNN to classify visible canine conditions
from smartphone photos (proposal §5.7.1). Serves a future
`app/features/vision_diagnosis/infrastructure/ml/engine.py` (see
`.agents/skills/ml-feature/SKILL.md` for the stub-vs-real engine pattern
that feature should follow once built).

- **Labels**: keep `LABELS` in `dataset.py` in sync with whatever
  `SUPPORTED_CONDITIONS` the serving engine ends up defining.
- **Data**: raw images are not committed to this repo (see root
  `.gitignore`'s `datasets/` entry) — point `train.py --data-dir` at wherever
  the 1,000–2,000 veterinarian-labelled images (proposal Table 4) are stored.
- **Explainability**: Grad-CAM generation belongs with the serving code
  (`app/features/vision_diagnosis/infrastructure/ml/`) once implemented,
  since it runs per-request against the loaded model, not during training.
- **Calibration**: fit `ml/common/metrics.py::TemperatureScaler` on the
  validation split after training and store the resulting temperature
  alongside the checkpoint (e.g. in a sibling `.json` metadata file).

## Usage (once real data is wired in)

```bash
pip install -r requirements-ml.txt   # from repo root
python -m ml.vision.train --data-dir /path/to/images --epochs 20 --out model_registry/vision/efficientnet_v1.pt
python -m ml.vision.evaluate --checkpoint model_registry/vision/efficientnet_v1.pt --data-dir /path/to/images
```

## Model versions

| Version | Trained on | Notes |
|---|---|---|
| _(none yet)_ | — | No serving feature exists yet either -- build `app/features/vision_diagnosis/` (see `.agents/skills/ml-feature/SKILL.md`), train a checkpoint here, then point its `VISION_MODEL_BACKEND` setting at it. |
