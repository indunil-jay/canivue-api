"""Evaluation entrypoint for the Multi-Task Canine Symptom Parser.

Computes:
1. Condition classification metrics (Macro-F1, Precision, Recall, Accuracy)
2. Expected Calibration Error (ECE from ml.common.metrics)
3. Token-level NER BIO classification metrics (Macro-F1, Accuracy)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ml.common.metrics import classification_metrics, expected_calibration_error
from ml.nlp.dataset import (
    MultiTaskSymptomDataset,
    get_dog_level_splits,
)
from ml.nlp.model import MultiTaskSymptomTransformer
from ml.nlp.seed_data import generate_seed_records, load_seed_dataset


def evaluate_nlp_model(
    model_dir: str = "model_registry/nlp/symptom_distilbert_v1",
    data_path: str | None = None,
    batch_size: int = 8,
) -> dict[str, float]:
    """Evaluate trained multi-task NLP checkpoint on held-out test split."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoTokenizer

    if data_path and Path(data_path).exists():
        records = load_seed_dataset(data_path)
    else:
        records = generate_seed_records(num_dogs=40, seed=42)

    _train_records, _val_records, test_records = get_dog_level_splits(records)

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    test_ds = MultiTaskSymptomDataset(test_records, tokenizer=tokenizer)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiTaskSymptomTransformer.from_pretrained(model_dir)
    model.to(device)
    model.eval()

    all_cond_true: list[int] = []
    all_cond_pred: list[int] = []
    all_cond_probs: list[float] = []

    all_ner_true: list[int] = []
    all_ner_pred: list[int] = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            ner_labels = batch["ner_labels"]
            condition_label = batch["condition_label"]

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)

            # Condition metrics
            cond_logits = outputs["condition_logits"]
            probs = torch.softmax(cond_logits, dim=-1)
            preds = torch.argmax(probs, dim=-1)

            for i in range(len(condition_label)):
                true_lbl = condition_label[i].item()
                pred_lbl = preds[i].item()
                prob = probs[i, pred_lbl].item()
                all_cond_true.append(true_lbl)
                all_cond_pred.append(pred_lbl)
                all_cond_probs.append(prob)

            # NER metrics (filter out -100)
            ner_logits = outputs["ner_logits"]
            ner_preds = torch.argmax(ner_logits, dim=-1)

            for i in range(len(ner_labels)):
                target_seq = ner_labels[i].tolist()
                pred_seq = ner_preds[i].tolist()
                for t, p in zip(target_seq, pred_seq):
                    if t != -100:
                        all_ner_true.append(t)
                        all_ner_pred.append(p)

    # Calculate metrics
    cond_metrics = classification_metrics(all_cond_true, all_cond_pred)
    ece = expected_calibration_error(all_cond_true, all_cond_probs)

    ner_metrics = classification_metrics(all_ner_true, all_ner_pred)

    results = {
        "condition_accuracy": cond_metrics["accuracy"],
        "condition_macro_f1": cond_metrics["f1_macro"],
        "condition_macro_precision": cond_metrics["precision_macro"],
        "condition_macro_recall": cond_metrics["recall_macro"],
        "condition_ece": ece,
        "ner_accuracy": ner_metrics["accuracy"],
        "ner_macro_f1": ner_metrics["f1_macro"],
    }

    print("\n--- Multi-Task NLP Evaluation Results ---")
    for k, v in results.items():
        print(f"  {k:30s}: {v:.4f}")
    print("-----------------------------------------\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate multi-task canine symptom NLP model")
    parser.add_argument("--model-dir", type=str, default="model_registry/nlp/symptom_distilbert_v1")
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    evaluate_nlp_model(
        model_dir=args.model_dir,
        data_path=args.data_path,
        batch_size=args.batch_size,
    )
