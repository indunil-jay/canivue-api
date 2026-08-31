# Behavioural (Sensor) Model

Trains a hybrid 1D-CNN-LSTM (or temporal Transformer) over fixed-length
windows of six-axis IMU data (Ax, Ay, Az, Gx, Gy, Gz) from the ESP32/MPU6050
collar (proposal §5.7.2). Serves a future
`app/features/behavioural_analysis/infrastructure/ml/engine.py`.

- **Windowing**: raw streams are cut into fixed windows (e.g. 10s at
  50–100Hz) in `dataset.py` before batching — this is the same "windowing"
  step the serving-side preprocessing must replicate exactly at inference
  time, so keep the window/stride constants in one place and import them
  from both `dataset.py` and the eventual serving `preprocessing.py`.
- **Sensor-quality gating**: packet-loss, signal clipping, and sampling-rate
  consistency (proposal §5.7.2) should be computed the same way here as in
  serving so training data quality matches what the model sees live.
- **Labels**: `Normal movement, Resting, Walking, Running, Excessive
  scratching, Head shaking, Limping/gait abnormality, Reduced activity` — see
  `dataset.py::BEHAVIOUR_LABELS`.
- **Data**: 30–50 dogs, repeated sessions, video-synchronized behaviour
  labels (proposal Table 4) — not committed to the repo (`.gitignore`'s
  `datasets/` entry).

## Usage (once real data is wired in)

```bash
pip install -r requirements-ml.txt   # from repo root
python -m ml.behavioural.train --data-dir /path/to/sensor_sessions --epochs 30 \
    --out model_registry/behavioural/cnn_lstm_v1.pt
```

## Model versions

| Version | Trained on | Notes |
|---|---|---|
| _(none yet)_ | — | Follow `ml/vision/train.py` as the worked reference for this training loop's shape. |
