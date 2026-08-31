"""Training entrypoint for the symptom-extraction / condition-classification NLP model.

Mirrors ml/vision/train.py's shape -- see that file for a fully worked-out
reference (build model -> dog-level split -> loop -> save checkpoint). Left
as a skeleton here since the exact task framing (joint vs. separate heads
for extraction and classification) is a design decision to make once real
annotated symptom data exists (proposal Phase 3).

    python -m ml.nlp.train --data-dir /path/to/symptom_records --epochs 5 \
        --out model_registry/nlp/symptom_bert_v1
"""

import argparse

from ml.nlp.dataset import CONDITION_LABELS


def build_model(num_classes: int, base_model_name: str = "distilbert-base-uncased"):
    from transformers import AutoModelForSequenceClassification

    return AutoModelForSequenceClassification.from_pretrained(
        base_model_name, num_labels=num_classes
    )


def train(data_dir: str, epochs: int, out_path: str) -> None:
    raise NotImplementedError(
        "Wire this up once real annotated symptom text is collected (proposal Phase 3): "
        "load records, dog-level split via ml/common/data_splitting.py (split by "
        "the pet the symptom report is about, not by record), fine-tune with the "
        "HuggingFace Trainer API, then model.save_pretrained(out_path)."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--out", default="model_registry/nlp/symptom_bert_v1")
    args = parser.parse_args()

    train(args.data_dir, args.epochs, args.out)
