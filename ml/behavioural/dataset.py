"""Windowed IMU dataset for the behavioural model.

Requires `requirements-ml.txt` (torch, numpy, pandas).
"""

from typing import List

# Keep in sync with the eventual app/features/behavioural_analysis serving engine.
BEHAVIOUR_LABELS: List[str] = [
    "normal_movement",
    "resting",
    "walking",
    "running",
    "excessive_scratching",
    "head_shaking",
    "gait_abnormality",
    "reduced_activity",
]

# Must match whatever the serving-side preprocessing uses at inference time.
WINDOW_SECONDS = 10
SAMPLE_RATE_HZ = 50


class ImuWindowDataset:
    """Expects a directory of per-session CSVs with columns:
    `timestamp,ax,ay,az,gx,gy,gz,pet_id,session_id`, plus a `labels.csv`
    mapping (session_id, window_start_s) -> label, produced by aligning
    video-synchronized behaviour annotations to the raw stream.

    Sensor-quality indicators (packet-loss rate, signal clipping, sampling-rate
    consistency -- proposal §5.7.2) should be computed per window here and
    stored alongside each window so low-quality windows can be filtered or
    weighted during training, mirroring what the serving quality-scorer does.
    """

    def __init__(self, data_dir: str, windows: List[dict]):
        self.data_dir = data_dir
        self.windows = windows

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int):
        import numpy as np
        import torch

        window = self.windows[idx]
        # TODO: load the six-axis slice for this window from `self.data_dir`,
        # band-pass/Kalman filter it, then normalize (proposal §5.6).
        six_axis_array = np.asarray(window["six_axis_data"], dtype="float32")
        tensor = torch.from_numpy(six_axis_array)
        label_idx = BEHAVIOUR_LABELS.index(window["label"])
        return tensor, label_idx
