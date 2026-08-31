"""Training entrypoint for the 1D-CNN-LSTM behavioural model.

Mirrors ml/vision/train.py's shape (build model -> split -> loop -> save
checkpoint) -- see that file for a fully worked-out reference. Left as a
skeleton here since the model architecture and windowing details depend on
the actual collar data format collected during proposal Phase 3.

    python -m ml.behavioural.train --data-dir /path/to/sensor_sessions --epochs 30 \
        --out model_registry/behavioural/cnn_lstm_v1.pt
"""

import argparse

from ml.behavioural.dataset import BEHAVIOUR_LABELS


def build_model(num_classes: int, num_axes: int = 6):
    """1D-CNN over each window for short-term motion patterns, feeding an
    LSTM (or temporal-attention block) over the resulting sequence for
    longer-range dependencies (proposal §5.7.2)."""
    import torch.nn as nn

    class CnnLstmBehaviourModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Sequential(
                nn.Conv1d(num_axes, 32, kernel_size=5, padding=2),
                nn.ReLU(),
                nn.Conv1d(32, 64, kernel_size=5, padding=2),
                nn.ReLU(),
            )
            self.lstm = nn.LSTM(input_size=64, hidden_size=64, batch_first=True)
            self.classifier = nn.Linear(64, num_classes)

        def forward(self, x):  # x: (batch, num_axes, timesteps)
            features = self.conv(x).transpose(1, 2)  # -> (batch, timesteps, channels)
            _, (hidden, _) = self.lstm(features)
            return self.classifier(hidden[-1])

    return CnnLstmBehaviourModel()


def train(data_dir: str, epochs: int, out_path: str) -> None:
    raise NotImplementedError(
        "Wire this up once real collar sessions are collected (proposal Phase 3): "
        "load windows via ImuWindowDataset, dog-level split via "
        "ml/common/data_splitting.py, then train/eval loop identical in shape "
        "to ml/vision/train.py."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--out", default="model_registry/behavioural/cnn_lstm_v1.pt")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.out)
