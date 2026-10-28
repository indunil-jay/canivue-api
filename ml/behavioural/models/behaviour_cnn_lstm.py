
import torch
import torch.nn as nn


class BehaviourCNNLSTM(nn.Module):
    """
    1D-CNN-LSTM model for six-axis canine
    behaviour sensor data.

    Input shape:
        (batch_size, 256, 6)

    Output shape:
        (batch_size, 5)

    Output values are class logits, not probabilities.
    """

    def __init__(
        self,
        input_channels=6,
        num_classes=5,
        lstm_hidden_size=64,
        dropout=0.3,
    ):
        super().__init__()

        self.input_channels = input_channels

        # Extract local motion patterns from sensor signals.
        self.cnn = nn.Sequential(
            nn.Conv1d(
                in_channels=input_channels,
                out_channels=32,
                kernel_size=7,
                padding=3,
            ),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Conv1d(
                in_channels=32,
                out_channels=64,
                kernel_size=5,
                padding=2,
            ),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),

            nn.Dropout(dropout),
        )

        # Learn temporal relationships between motion features.
        self.lstm = nn.LSTM(
            input_size=64,
            hidden_size=lstm_hidden_size,
            num_layers=1,
            batch_first=True,
        )

        # Map learned features to the five planned classes.
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(lstm_hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, num_classes),
        )

    def forward(self, x):
        # Expected input: (batch, time_steps, channels)
        if x.ndim != 3:
            raise ValueError(
                "Expected input shape (batch, time_steps, channels)"
            )

        if x.shape[-1] != self.input_channels:
            raise ValueError(
                f"Expected {self.input_channels} sensor channels, "
                f"received {x.shape[-1]}"
            )

        # Conv1d expects (batch, channels, time_steps).
        x = x.transpose(1, 2)

        # Example: (B, 6, 256) -> (B, 64, 64).
        x = self.cnn(x)

        # LSTM expects (batch, time_steps, features).
        x = x.transpose(1, 2)

        # Example: (B, 64, 64) -> (B, 64, hidden_size).
        sequence_output, _ = self.lstm(x)

        # Use the final LSTM time step for classification.
        final_features = sequence_output[:, -1, :]

        # Return one logit per behaviour class.
        logits = self.classifier(final_features)

        return logits
