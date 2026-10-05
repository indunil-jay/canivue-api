"""Training pipeline for Multi-Task DistilBERT Canine Symptom Parser.

Trains the shared transformer on:
1. Token classification (BIO entity extraction) with Loss_NER
2. Sequence classification (4-class condition prediction) with Loss_condition
Joint loss: L = alpha * L_NER + beta * L_condition (default 0.6 / 0.4)

Checkpoint is exported to model_registry/nlp/ for production serving.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ml.nlp.dataset import (
    MultiTaskSymptomDataset,
    get_dog_level_splits,
)
from ml.nlp.model import MultiTaskSymptomTransformer
from ml.nlp.seed_data import generate_seed_records, load_seed_dataset


def train_multitask_nlp(
    data_path: str | None = None,
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 3e-5,
    alpha: float = 0.6,
    beta: float = 0.4,
    out_dir: str = "model_registry/nlp/symptom_distilbert_v1",
) -> dict[str, Any]:
    """Execute dog-level split, multi-task fine-tuning, and model export."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoTokenizer

    # 1. Load or generate records
    if data_path and Path(data_path).exists():
        records = load_seed_dataset(data_path)
    else:
        records = generate_seed_records(num_dogs=40, seed=42)

    # 2. Dog-level split (70% train, 15% val, 15% test)
    train_records, val_records, _test_records = get_dog_level_splits(records)

    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    train_ds = MultiTaskSymptomDataset(train_records, tokenizer=tokenizer)
    val_ds = MultiTaskSymptomDataset(val_records, tokenizer=tokenizer)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiTaskSymptomTransformer(base_model_name="distilbert-base-uncased")
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    history = {"train_loss": [], "val_loss": []}

    print(
        f"Training MultiTaskSymptomTransformer: {len(train_records)} train records, "
        f"{len(val_records)} val records on {device}"
    )

    for epoch in range(1, epochs + 1):
        model.train()
        total_train_loss = 0.0

        for batch in train_loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            ner_labels = batch["ner_labels"].to(device)
            condition_label = batch["condition_label"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                ner_labels=ner_labels,
                condition_label=condition_label,
                alpha=alpha,
                beta=beta,
            )

            loss = outputs["loss"]
            loss.backward()
            optimizer.step()
            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / max(1, len(train_loader))

        # Validation
        model.eval()
        total_val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                ner_labels = batch["ner_labels"].to(device)
                condition_label = batch["condition_label"].to(device)

                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    ner_labels=ner_labels,
                    condition_label=condition_label,
                    alpha=alpha,
                    beta=beta,
                )
                total_val_loss += outputs["loss"].item()

        avg_val_loss = total_val_loss / max(1, len(val_loader))
        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)

        print(
            f"Epoch {epoch}/{epochs} - Train Loss: {avg_train_loss:.4f} - Val Loss: {avg_val_loss:.4f}"
        )

    # 3. Export to model_registry/nlp
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(out_path)
    tokenizer.save_pretrained(out_path)
    print(f"Model and tokenizer exported successfully to: {out_path}")

    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train multi-task canine symptom NLP model")
    parser.add_argument("--data-path", type=str, default="data/seed_symptoms.jsonl")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--alpha", type=float, default=0.6)
    parser.add_argument("--beta", type=float, default=0.4)
    parser.add_argument("--out-dir", type=str, default="model_registry/nlp/symptom_distilbert_v1")
    args = parser.parse_args()

    train_multitask_nlp(
        data_path=args.data_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        alpha=args.alpha,
        beta=args.beta,
        out_dir=args.out_dir,
    )
