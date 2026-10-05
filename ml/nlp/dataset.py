"""Multi-task symptom dataset and token alignment for Transformer training.

Features:
- Standard 4-class condition labels matching production API
- 13-tag BIO entity labeling taxonomy
- Subword token-to-character span alignment (with -100 for ignored/special tokens)
- Dog-level dataset splitting to guarantee zero pet observation leakage
"""

from __future__ import annotations

from typing import Any

from ml.common.data_splitting import train_val_test_split

CONDITION_LABELS: list[str] = [
    "ear_inflammation",
    "skin_condition",
    "eye_condition",
    "other",
]

NER_LABELS: list[str] = [
    "O",
    "B-symptom",
    "I-symptom",
    "B-body_location",
    "I-body_location",
    "B-duration",
    "I-duration",
    "B-severity",
    "I-severity",
    "B-frequency",
    "I-frequency",
    "B-progression",
    "I-progression",
]

LABEL2ID: dict[str, int] = {lbl: i for i, lbl in enumerate(NER_LABELS)}
ID2LABEL: dict[int, str] = {i: lbl for i, lbl in enumerate(NER_LABELS)}

CONDITION2ID: dict[str, int] = {lbl: i for i, lbl in enumerate(CONDITION_LABELS)}
ID2CONDITION: dict[int, str] = {i: lbl for i, lbl in enumerate(CONDITION_LABELS)}


def align_tokens_and_bio_labels(
    text: str,
    spans: list[dict[str, Any]],
    offset_mapping: list[tuple[int, int]],
) -> list[int]:
    """Align character-level entity spans to subword token offsets using BIO scheme.

    Tokens with offset (0, 0) (such as [CLS], [SEP], padding) are assigned -100 so
    PyTorch CrossEntropyLoss ignores them during backpropagation.
    """
    labels: list[int] = []

    for token_start, token_end in offset_mapping:
        if token_start == token_end:
            # Special or padding token
            labels.append(-100)
            continue

        matched_label = "O"
        for span in spans:
            span_start = span["start"]
            span_end = span["end"]
            entity = span["entity"]

            if token_start >= span_start and token_end <= span_end:
                # Token is inside span
                is_start = token_start == span_start
                prefix = "B-" if is_start else "I-"
                candidate = f"{prefix}{entity}"
                if candidate in LABEL2ID:
                    matched_label = candidate
                break

        labels.append(LABEL2ID[matched_label])

    return labels


def get_dog_level_splits(
    records: list[dict[str, Any]],
    pet_id_key: str = "pet_id",
    ratios: dict[str, float] | None = None,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Split records into (train, val, test) splits partitioned by pet_id."""
    ratios_dict = ratios or {"train": 0.7, "val": 0.15, "test": 0.15}
    return train_val_test_split(records, pet_id_key=pet_id_key, ratios=ratios_dict, seed=seed)


class MultiTaskSymptomDataset:
    """PyTorch Dataset for multi-task symptom token classification & condition classification."""

    def __init__(
        self,
        records: list[dict[str, Any]],
        tokenizer: Any = None,
        tokenizer_name: str = "distilbert-base-uncased",
        max_length: int = 128,
    ):
        self.records = records
        self.max_length = max_length

        if tokenizer is not None:
            self.tokenizer = tokenizer
        else:
            try:
                from transformers import AutoTokenizer

                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
            except (ImportError, OSError, RuntimeError):
                self.tokenizer = None

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        if self.tokenizer is None:
            raise RuntimeError("Transformers AutoTokenizer is not installed or available.")

        import torch

        record = self.records[idx]
        text = record["text"]
        spans = record.get("spans", [])
        condition_label = record["condition_label"]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_offsets_mapping=True,
            return_tensors="pt",
        )

        offset_mapping = encoding.pop("offset_mapping")[0].tolist()
        ner_labels = align_tokens_and_bio_labels(text, spans, offset_mapping)

        # Pad / truncate ner_labels to match max_length exactly
        if len(ner_labels) < self.max_length:
            ner_labels = ner_labels + [-100] * (self.max_length - len(ner_labels))
        else:
            ner_labels = ner_labels[: self.max_length]

        condition_id = CONDITION2ID[condition_label]

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "ner_labels": torch.tensor(ner_labels, dtype=torch.long),
            "condition_label": torch.tensor(condition_id, dtype=torch.long),
        }
