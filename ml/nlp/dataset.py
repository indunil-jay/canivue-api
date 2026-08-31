"""Symptom-description dataset for the NLP model.

Requires `requirements-ml.txt` (transformers, tokenizers).
"""

from typing import List

# Standardized symptom-category ontology (proposal §5.7.3) -- keep in sync with
# the eventual app/features/symptom_nlp serving engine.
CONDITION_LABELS: List[str] = [
    "ear_inflammation",
    "skin_condition",
    "eye_condition",
    "other_condition",
]


class SymptomTextDataset:
    """Expects a CSV/JSONL with columns:
    `text,pet_id,condition_label,symptom_spans` where `symptom_spans` is a
    list of (start, end, entity_type) tuples for the information-extraction
    task (entity_type in {symptom, body_location, duration, severity, ...}).

    Example row (proposal §5.7.3):
        text: "My dog has been scratching its left ear for three days and
               it is becoming red."
        condition_label: ear_inflammation
        symptom_spans: [(15, 25, "symptom"), (34, 43, "body_location"), ...]
    """

    def __init__(self, records: List[dict], tokenizer_name: str = "distilbert-base-uncased"):
        from transformers import AutoTokenizer

        self.records = records
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int):
        record = self.records[idx]
        encoding = self.tokenizer(
            record["text"], truncation=True, padding="max_length", max_length=128, return_tensors="pt"
        )
        label_idx = CONDITION_LABELS.index(record["condition_label"])
        return {k: v.squeeze(0) for k, v in encoding.items()}, label_idx
