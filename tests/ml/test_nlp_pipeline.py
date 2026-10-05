"""Tests for ml/nlp multi-task offline training pipeline."""

from ml.nlp.dataset import (
    CONDITION_LABELS,
    LABEL2ID,
    align_tokens_and_bio_labels,
    get_dog_level_splits,
)
from ml.nlp.seed_data import compute_spans, generate_seed_records


def test_seed_records_generation_and_spans():
    """Verify generated seed records have correct fields and span offsets match raw text."""
    records = generate_seed_records(num_dogs=10, seed=123)
    assert len(records) >= 10

    for rec in records:
        assert "record_id" in rec
        assert "pet_id" in rec
        assert "text" in rec
        assert rec["condition_label"] in CONDITION_LABELS
        assert "spans" in rec
        assert isinstance(rec["spans"], list)

        # Verify each span matches the exact substring in rec["text"]
        for span in rec["spans"]:
            start = span["start"]
            end = span["end"]
            assert rec["text"][start:end] == span["text"]
            assert span["entity"] in {
                "symptom",
                "body_location",
                "duration",
                "frequency",
                "progression",
                "severity",
            }


def test_dog_level_data_splitting_no_leakage():
    """Verify that records for the same pet_id never appear in multiple splits."""
    records = generate_seed_records(num_dogs=30, seed=42)
    train_recs, val_recs, test_recs = get_dog_level_splits(records)

    train_pets = {r["pet_id"] for r in train_recs}
    val_pets = {r["pet_id"] for r in val_recs}
    test_pets = {r["pet_id"] for r in test_recs}

    # Verify zero intersection between any two splits
    assert len(train_pets.intersection(val_pets)) == 0
    assert len(train_pets.intersection(test_pets)) == 0
    assert len(val_pets.intersection(test_pets)) == 0

    # Verify all records are accounted for
    assert len(train_recs) + len(val_recs) + len(test_recs) == len(records)


def test_bio_token_alignment():
    """Verify subword token alignment produces valid BIO labels and -100 for specials."""
    text = "Dog scratching left ear"
    # Entities: scratching (4, 14), left ear (15, 23)
    spans = [
        {"start": 4, "end": 14, "entity": "symptom"},
        {"start": 15, "end": 23, "entity": "body_location"},
    ]
    # Simulated offset mapping for: [CLS], Dog, scratch, ##ing, left, ear, [SEP]
    offset_mapping = [
        (0, 0),  # [CLS]
        (0, 3),  # Dog
        (4, 11),  # scratch
        (11, 14),  # ##ing
        (15, 19),  # left
        (20, 23),  # ear
        (0, 0),  # [SEP]
    ]

    labels = align_tokens_and_bio_labels(text, spans, offset_mapping)

    assert labels[0] == -100  # [CLS]
    assert labels[1] == LABEL2ID["O"]  # Dog
    assert labels[2] == LABEL2ID["B-symptom"]  # scratch
    assert labels[3] == LABEL2ID["I-symptom"]  # ##ing
    assert labels[4] == LABEL2ID["B-body_location"]  # left
    assert labels[5] == LABEL2ID["I-body_location"]  # ear
    assert labels[6] == -100  # [SEP]


def test_compute_spans_helper():
    """Verify compute_spans finds correct character indices."""
    text = "Scratching its ear for 3 days."
    entities = [
        {"entity": "symptom", "text": "Scratching"},
        {"entity": "body_location", "text": "ear"},
        {"entity": "duration", "text": "3 days"},
    ]
    spans = compute_spans(text, entities)

    assert len(spans) == 3
    assert spans[0]["text"] == "Scratching"
    assert spans[0]["start"] == 0
    assert spans[0]["end"] == 10
    assert spans[1]["text"] == "ear"
    assert spans[2]["text"] == "3 days"
