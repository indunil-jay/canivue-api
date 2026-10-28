
# ============================================================
# CANIVUE: CANINE BEHAVIOUR SENSOR MODEL TRAINING
# Architecture: 1D-CNN-LSTM
# Framework: PyTorch
# ============================================================

from copy import deepcopy
from pathlib import Path
import random

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from behaviour_cnn_lstm import BehaviourCNNLSTM


# ============================================================
# 1. CONFIGURATION
# ============================================================

SEED = 42

WINDOW_SIZE = 256
CHANNELS = 6

BATCH_SIZE = 32
EPOCHS = 100
LEARNING_RATE = 0.001
PATIENCE = 10

CLASSES = [
    "rest",
    "walking",
    "running",
    "scratching",
    "head_shaking",
]

BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    BASE_DIR
    / "data_logger"
    / "data"
    / "processed"
    / "ml_dataset.npz"
)

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "behaviour_cnn_lstm_best.pt"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# 2. REPRODUCIBILITY
# ============================================================

def set_seed(seed=SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ============================================================
# 3. LOAD AND VALIDATE THE PREPARED DATASET
# ============================================================

def load_dataset():

    print("\nChecking prepared dataset...")

    if not DATASET_PATH.exists():

        print("\nNo prepared canine ML dataset found.")
        print("Expected file:", DATASET_PATH)

        print(
            "\nYour current engineering recordings are "
            "correctly excluded from model training."
        )

        return None

    required_keys = [
        "X_train",
        "X_val",
        "X_test",
        "y_train",
        "y_val",
        "y_test",
        "mean",
        "std",
    ]

    try:
        with np.load(
            DATASET_PATH,
            allow_pickle=False
        ) as data:

            missing_keys = [
                key for key in required_keys
                if key not in data.files
            ]

            if missing_keys:
                print(
                    "Dataset is missing required arrays:",
                    missing_keys
                )
                return None

            dataset = {
                key: data[key].copy()
                for key in required_keys
            }

    except (OSError, ValueError) as error:

        print("Unable to read dataset:", error)
        return None

    # --------------------------------------------------------
    # Validate each split
    # --------------------------------------------------------

    for split in ["train", "val", "test"]:

        X = dataset[f"X_{split}"]
        y = dataset[f"y_{split}"]

        print(
            f"{split.upper()} shapes: "
            f"X={X.shape}, y={y.shape}"
        )

        if len(X) == 0 or len(y) == 0:

            print(f"ERROR: {split} split is empty.")
            return None

        if X.ndim != 3:

            print(
                f"ERROR: {split} inputs must be "
                "(samples, time steps, channels)."
            )
            return None

        if X.shape[1:] != (WINDOW_SIZE, CHANNELS):

            print(
                f"ERROR: Incorrect {split} input shape:",
                X.shape
            )

            print(
                f"Expected (samples, "
                f"{WINDOW_SIZE}, {CHANNELS})."
            )

            return None

        if len(X) != len(y):

            print(
                f"ERROR: Input and label counts differ "
                f"in {split}."
            )

            return None

        if not np.issubdtype(y.dtype, np.str_):

            print(
                f"ERROR: {split} labels must be "
                "behaviour-name strings."
            )

            return None

        if not np.isfinite(X).all():

            print(
                f"ERROR: Non-finite values found "
                f"in {split}."
            )

            return None

        unexpected_labels = (
            set(y.tolist()) - set(CLASSES)
        )

        if unexpected_labels:

            print(
                f"ERROR: Unexpected labels in {split}:",
                sorted(unexpected_labels)
            )

            return None

    # --------------------------------------------------------
    # Validate normalization parameters
    # --------------------------------------------------------

    mean = np.asarray(
        dataset["mean"],
        dtype=np.float32
    )

    std = np.asarray(
        dataset["std"],
        dtype=np.float32
    )

    if mean.shape != (CHANNELS,):

        print(
            "ERROR: Normalization mean must contain "
            f"{CHANNELS} values."
        )

        return None

    if std.shape != (CHANNELS,):

        print(
            "ERROR: Normalization standard deviation "
            f"must contain {CHANNELS} values."
        )

        return None

    if (
        not np.isfinite(mean).all()
        or not np.isfinite(std).all()
    ):

        print(
            "ERROR: Normalization parameters "
            "contain non-finite values."
        )

        return None

    if np.any(std <= 0):

        print(
            "ERROR: Normalization standard deviations "
            "must be greater than zero."
        )

        return None

    dataset["mean"] = mean
    dataset["std"] = std

    # --------------------------------------------------------
    # Confirm all five classes occur in training data
    # --------------------------------------------------------

    training_classes = set(
        dataset["y_train"].tolist()
    )

    missing_training_classes = (
        set(CLASSES) - training_classes
    )

    if missing_training_classes:

        print("\nTraining cannot proceed.")

        print(
            "Missing classes in training data:",
            sorted(missing_training_classes)
        )

        print(
            "Collect more verified canine recordings "
            "before training."
        )

        return None

    # Warn if validation or test data lacks classes.
    for split in ["val", "test"]:

        present_classes = set(
            dataset[f"y_{split}"].tolist()
        )

        missing_classes = (
            set(CLASSES) - present_classes
        )

        if missing_classes:

            print(
                f"WARNING: {split} split is missing "
                f"classes: {sorted(missing_classes)}"
            )

            print(
                "Class-specific evaluation will be "
                "incomplete for this split."
            )

    print("\nDataset validation passed.")

    return dataset


# ============================================================
# 4. CONVERT DATA TO PYTORCH DATALOADERS
# ============================================================

def make_loader(X, y, shuffle=False):

    class_to_index = {
        label: index
        for index, label in enumerate(CLASSES)
    }

    encoded_labels = np.array(
        [
            class_to_index[label]
            for label in y.tolist()
        ],
        dtype=np.int64
    )

    features = torch.from_numpy(
        X.astype(np.float32, copy=False)
    )

    targets = torch.from_numpy(
        encoded_labels
    )

    dataset = TensorDataset(
        features,
        targets
    )

    return DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=shuffle,
        num_workers=0
    )


# ============================================================
# 5. TRAIN OR VALIDATE ONE EPOCH
# ============================================================

def run_epoch(
    model,
    loader,
    criterion,
    optimizer=None
):

    is_training = optimizer is not None

    if is_training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    correct_predictions = 0
    total_samples = 0

    with torch.set_grad_enabled(is_training):

        for X_batch, y_batch in loader:

            X_batch = X_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            if is_training:
                optimizer.zero_grad()

            logits = model(X_batch)

            loss = criterion(
                logits,
                y_batch
            )

            if is_training:

                loss.backward()

                optimizer.step()

            batch_size = y_batch.size(0)

            total_loss += (
                loss.item() * batch_size
            )

            predictions = torch.argmax(
                logits,
                dim=1
            )

            correct_predictions += (
                predictions == y_batch
            ).sum().item()

            total_samples += batch_size

    if total_samples == 0:
        raise ValueError("Cannot evaluate an empty data loader.")

    average_loss = total_loss / total_samples

    accuracy = (
        correct_predictions / total_samples
    )

    return average_loss, accuracy


# ============================================================
# 6. EVALUATE THE HELD-OUT TEST SET
# ============================================================

def evaluate_test_set(model, loader):

    number_of_classes = len(CLASSES)

    confusion_matrix = np.zeros(
        (number_of_classes, number_of_classes),
        dtype=np.int64
    )

    model.eval()

    with torch.no_grad():

        for X_batch, y_batch in loader:

            X_batch = X_batch.to(DEVICE)

            logits = model(X_batch)

            predictions = (
                logits.argmax(dim=1)
                .cpu()
                .numpy()
            )

            actual_labels = (
                y_batch.numpy()
            )

            for actual, predicted in zip(
                actual_labels,
                predictions
            ):

                confusion_matrix[
                    actual,
                    predicted
                ] += 1

    total = confusion_matrix.sum()

    if total == 0:

        print(
            "\nTest evaluation skipped: "
            "the test set is empty."
        )

        return

    accuracy = (
        np.trace(confusion_matrix) / total
    )

    print("\n" + "=" * 60)
    print("HELD-OUT TEST SET EVALUATION")
    print("=" * 60)

    print(f"Accuracy: {accuracy:.4f}")

    precision_scores = []
    recall_scores = []
    f1_scores = []

    print("\nClass-wise results:")

    for index, class_name in enumerate(CLASSES):

        true_positive = confusion_matrix[
            index, index
        ]

        predicted_count = confusion_matrix[
            :, index
        ].sum()

        actual_count = confusion_matrix[
            index, :
        ].sum()

        precision = (
            true_positive / predicted_count
            if predicted_count > 0
            else 0.0
        )

        recall = (
            true_positive / actual_count
            if actual_count > 0
            else 0.0
        )

        if precision + recall > 0:

            f1 = (
                2 * precision * recall
                / (precision + recall)
            )

        else:
            f1 = 0.0

        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)

        print(
            f"{class_name:15s} "
            f"Precision={precision:.3f}  "
            f"Recall={recall:.3f}  "
            f"F1={f1:.3f}  "
            f"Support={actual_count}"
        )

    print(
        "\nMacro precision: "
        f"{np.mean(precision_scores):.4f}"
    )

    print(
        "Macro recall: "
        f"{np.mean(recall_scores):.4f}"
    )

    print(
        "Macro F1-score: "
        f"{np.mean(f1_scores):.4f}"
    )

    print("\nConfusion matrix:")
    print("Rows = actual classes")
    print("Columns = predicted classes")
    print("Class order:", CLASSES)
    print(confusion_matrix)

    # Save a machine-readable evaluation result.
    report_path = (
        Path(__file__).resolve().parent
        / "test_evaluation.txt"
    )

    with report_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "CANIVUE TEST SET EVALUATION\n"
        )

        file.write(
            f"Accuracy: {accuracy:.4f}\n"
        )

        file.write(
            f"Macro precision: "
            f"{np.mean(precision_scores):.4f}\n"
        )

        file.write(
            f"Macro recall: "
            f"{np.mean(recall_scores):.4f}\n"
        )

        file.write(
            f"Macro F1-score: "
            f"{np.mean(f1_scores):.4f}\n"
        )

        file.write(
            "\nClass order: "
            + ", ".join(CLASSES)
            + "\n"
        )

        file.write(
            "\nConfusion matrix:\n"
        )

        file.write(
            np.array2string(confusion_matrix)
        )

    print("\nEvaluation report saved to:", report_path)


# ============================================================
# 7. MAIN TRAINING PIPELINE
# ============================================================

def main():

    set_seed()

    print("=" * 60)
    print("CANIVUE BEHAVIOUR MODEL TRAINING")
    print("=" * 60)

    print("Device:", DEVICE)
    print("Architecture: 1D-CNN-LSTM")
    print("Window size:", WINDOW_SIZE)
    print("Sensor channels:", CHANNELS)
    print("Classes:", CLASSES)

    # Load and validate the prepared dataset.
    dataset = load_dataset()

    if dataset is None:

        print("\nTraining stopped safely.")
        return

    # Arrays are already normalized by
    # prepare_ml_dataset.py.
    # Do not normalize them a second time.

    train_loader = make_loader(
        dataset["X_train"],
        dataset["y_train"],
        shuffle=True
    )

    val_loader = make_loader(
        dataset["X_val"],
        dataset["y_val"],
        shuffle=False
    )

    test_loader = make_loader(
        dataset["X_test"],
        dataset["y_test"],
        shuffle=False
    )

    # --------------------------------------------------------
    # Initialize the model
    # --------------------------------------------------------

    model = BehaviourCNNLSTM(
        input_channels=CHANNELS,
        num_classes=len(CLASSES)
    ).to(DEVICE)

    criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-4
    )

    print("\nTraining configuration")
    print("-" * 40)

    print(
        "Training windows:",
        len(dataset["X_train"])
    )

    print(
        "Validation windows:",
        len(dataset["X_val"])
    )

    print(
        "Test windows:",
        len(dataset["X_test"])
    )

    # --------------------------------------------------------
    # Training with early stopping
    # --------------------------------------------------------

    best_val_loss = float("inf")
    best_state = None

    epochs_without_improvement = 0

    for epoch in range(1, EPOCHS + 1):

        train_loss, train_accuracy = run_epoch(
            model,
            train_loader,
            criterion,
            optimizer
        )

        val_loss, val_accuracy = run_epoch(
            model,
            val_loader,
            criterion
        )

        print(
            f"Epoch {epoch:03d}/{EPOCHS} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Train Acc: {train_accuracy:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_accuracy:.4f}"
        )

        # Select the checkpoint using validation loss only.
        if val_loss < best_val_loss:

            best_val_loss = val_loss

            best_state = deepcopy(
                model.state_dict()
            )

            epochs_without_improvement = 0

        else:

            epochs_without_improvement += 1

        if epochs_without_improvement >= PATIENCE:

            print(
                f"\nEarly stopping after epoch {epoch}."
            )

            break

    if best_state is None:

        print(
            "\nTraining did not produce a valid checkpoint."
        )

        return

    # --------------------------------------------------------
    # Save the best model and preprocessing parameters
    # --------------------------------------------------------

    model.load_state_dict(best_state)

    checkpoint = {
        "model_state_dict": best_state,

        "classes": CLASSES,

        "input_shape": [
            WINDOW_SIZE,
            CHANNELS
        ],

        "normalization_mean": (
            dataset["mean"].tolist()
        ),

        "normalization_std": (
            dataset["std"].tolist()
        ),

        "best_validation_loss": float(
            best_val_loss
        ),

        "architecture": "1D-CNN-LSTM",

        "seed": SEED,
    }

    torch.save(
        checkpoint,
        MODEL_PATH
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETED")
    print("=" * 60)

    print("Best validation loss:", round(best_val_loss, 4))
    print("Model saved to:", MODEL_PATH)

    print(
        "Normalization parameters saved with checkpoint."
    )

    # --------------------------------------------------------
    # Final evaluation on the held-out test set
    # --------------------------------------------------------

    evaluate_test_set(
        model,
        test_loader
    )


# ============================================================
# 8. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
