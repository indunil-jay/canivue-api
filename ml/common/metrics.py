"""Evaluation metrics shared across modalities (proposal §5.9, Table 6).

Kept dependency-light (only needs `scikit-learn`, already in
requirements-ml.txt) so it can be imported from any modality's
`evaluate.py` without extra setup.
"""

from typing import Dict, List, Sequence


def classification_metrics(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, float]:
    """Accuracy, precision, recall, F1 -- the current-diagnosis evaluation set."""
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def roc_auc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Binary/one-vs-rest ROC-AUC, used for both diagnostic and progression evaluation."""
    from sklearn.metrics import roc_auc_score

    return roc_auc_score(y_true, y_score)


def brier_score(y_true: Sequence[int], y_prob: Sequence[float]) -> float:
    """Calibration quality of predicted probabilities -- required for DPRPE evaluation."""
    from sklearn.metrics import brier_score_loss

    return brier_score_loss(y_true, y_prob)


def expected_calibration_error(
    y_true: Sequence[int], y_prob: Sequence[float], n_bins: int = 10
) -> float:
    """Mean gap between predicted confidence and observed accuracy, bucketed into `n_bins`."""
    import numpy as np

    y_true_arr = np.asarray(y_true, dtype=float)
    y_prob_arr = np.asarray(y_prob, dtype=float)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for lo, hi in zip(bin_edges[:-1], bin_edges[1:]):
        in_bin = (y_prob_arr > lo) & (y_prob_arr <= hi)
        if not in_bin.any():
            continue
        bin_confidence = y_prob_arr[in_bin].mean()
        bin_accuracy = y_true_arr[in_bin].mean()
        ece += (in_bin.sum() / len(y_prob_arr)) * abs(bin_confidence - bin_accuracy)

    return float(ece)


def false_reassurance_rate(y_true_deteriorated: Sequence[int], y_pred_low_risk: Sequence[int]) -> float:
    """Fraction of cases that actually deteriorated but were predicted low-risk (DPRPE safety metric).

    `y_true_deteriorated[i]` is 1 if the dog's outcome was slow/rapid/critical deterioration.
    `y_pred_low_risk[i]` is 1 if the model classified that case as low risk.
    This is the metric the proposal flags as safety-critical: a false reassurance
    means an owner was told "low risk" when the dog actually got worse.
    """
    deteriorated_indices = [i for i, v in enumerate(y_true_deteriorated) if v == 1]
    if not deteriorated_indices:
        return 0.0
    false_reassurances = sum(1 for i in deteriorated_indices if y_pred_low_risk[i] == 1)
    return false_reassurances / len(deteriorated_indices)


class TemperatureScaler:
    """Post-hoc calibration for overconfident neural-network softmax outputs.

    Proposal §5.7.1: "a calibration method such as temperature scaling will
    be evaluated before these probabilities are presented as confidence
    values." Fit `temperature` on a held-out validation split, then divide
    logits by it before the final softmax at inference time.
    """

    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature

    def fit(self, logits, labels, lr: float = 0.01, max_iter: int = 50) -> "TemperatureScaler":
        """Optimize a single scalar temperature via LBFGS. Requires torch (requirements-ml.txt)."""
        import torch

        logits_t = torch.as_tensor(logits, dtype=torch.float32)
        labels_t = torch.as_tensor(labels, dtype=torch.long)
        temperature = torch.nn.Parameter(torch.ones(1) * self.temperature)
        optimizer = torch.optim.LBFGS([temperature], lr=lr, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            loss = torch.nn.functional.cross_entropy(logits_t / temperature, labels_t)
            loss.backward()
            return loss

        optimizer.step(closure)
        self.temperature = float(temperature.detach().clamp(min=1e-3))
        return self

    def calibrate(self, logits):
        import torch

        logits_t = torch.as_tensor(logits, dtype=torch.float32)
        return torch.softmax(logits_t / self.temperature, dim=-1)
