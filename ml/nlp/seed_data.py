"""Seed dataset generator for canine symptom NLP multi-task model.

Generates realistic veterinary clinical observations and owner reports across
multiple canine patients, with dog-level identifiers (`pet_id`) for leakage-free splitting,
character-level entity spans (symptoms, body locations, duration, frequency, progression),
and 4-class condition labels.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

# Standard 4-class condition taxonomy
CONDITION_CATEGORIES = [
    "ear_inflammation",
    "skin_condition",
    "eye_condition",
    "other",
]

RAW_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "ear_inflammation": [
        {
            "text": "My dog has been scratching its left ear for three days and it is becoming red.",
            "entities": [
                {"entity": "symptom", "text": "scratching"},
                {"entity": "body_location", "text": "left ear"},
                {"entity": "duration", "text": "three days"},
                {"entity": "symptom", "text": "red"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Vigorous head shaking and dark brown discharge from right ear since yesterday.",
            "entities": [
                {"entity": "symptom", "text": "head shaking"},
                {"entity": "symptom", "text": "discharge"},
                {"entity": "body_location", "text": "right ear"},
                {"entity": "duration", "text": "since yesterday"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Strong foul odor and constant scratching of both ears for 1 week.",
            "entities": [
                {"entity": "symptom", "text": "odor"},
                {"entity": "frequency", "text": "constant"},
                {"entity": "symptom", "text": "scratching"},
                {"entity": "body_location", "text": "both ears"},
                {"entity": "duration", "text": "1 week"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Severe swelling and pain around the ear canal, getting worse since this morning.",
            "entities": [
                {"entity": "symptom", "text": "swelling"},
                {"entity": "body_location", "text": "ear"},
                {"entity": "progression", "text": "getting worse"},
                {"entity": "duration", "text": "since this morning"},
            ],
            "is_emergency": False,
        },
    ],
    "skin_condition": [
        {
            "text": "Intense itching and red patches on belly and back for 2 weeks.",
            "entities": [
                {"entity": "symptom", "text": "itching"},
                {"entity": "symptom", "text": "red"},
                {"entity": "body_location", "text": "belly"},
                {"entity": "body_location", "text": "back"},
                {"entity": "duration", "text": "2 weeks"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Significant hair loss and flaky skin around paw, no vomiting.",
            "entities": [
                {"entity": "symptom", "text": "hair loss"},
                {"entity": "body_location", "text": "skin"},
                {"entity": "body_location", "text": "paw"},
                {"entity": "symptom", "text": "vomiting", "negated": True},
            ],
            "is_emergency": False,
        },
        {
            "text": "Dog has pustules and redness on skin constantly spreading for 5 days.",
            "entities": [
                {"entity": "symptom", "text": "redness"},
                {"entity": "body_location", "text": "skin"},
                {"entity": "frequency", "text": "constantly"},
                {"entity": "progression", "text": "spreading"},
                {"entity": "duration", "text": "5 days"},
            ],
            "is_emergency": False,
        },
    ],
    "eye_condition": [
        {
            "text": "Cloudy eye and green discharge from right eye for three days.",
            "entities": [
                {"entity": "symptom", "text": "Cloudy eye"},
                {"entity": "symptom", "text": "discharge"},
                {"entity": "body_location", "text": "right eye"},
                {"entity": "duration", "text": "three days"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Watery eyes and squinting in left eye since yesterday morning.",
            "entities": [
                {"entity": "symptom", "text": "Watery eyes"},
                {"entity": "body_location", "text": "left eye"},
                {"entity": "duration", "text": "since yesterday"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Redness and swelling around both eyes getting worse for 4 days.",
            "entities": [
                {"entity": "symptom", "text": "Redness"},
                {"entity": "symptom", "text": "swelling"},
                {"entity": "body_location", "text": "both eyes"},
                {"entity": "progression", "text": "getting worse"},
                {"entity": "duration", "text": "4 days"},
            ],
            "is_emergency": False,
        },
    ],
    "other": [
        {
            "text": "Dog is limping on right leg and lethargic for two days.",
            "entities": [
                {"entity": "symptom", "text": "limping"},
                {"entity": "body_location", "text": "right leg"},
                {"entity": "symptom", "text": "lethargic"},
                {"entity": "duration", "text": "two days"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Repeated vomiting and diarrhea since last night, reduced activity.",
            "entities": [
                {"entity": "symptom", "text": "vomiting"},
                {"entity": "symptom", "text": "diarrhea"},
                {"entity": "symptom", "text": "reduced activity"},
            ],
            "is_emergency": False,
        },
        {
            "text": "Emergency: my dog collapsed and is struggling to breathe right now.",
            "entities": [
                {"entity": "symptom", "text": "collapsed"},
                {"entity": "symptom", "text": "struggling to breathe"},
            ],
            "is_emergency": True,
        },
    ],
}


def compute_spans(text: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute and verify exact [start, end] character offsets for target entities."""
    spans: list[dict[str, Any]] = []
    text_lower = text.lower()

    for ent in entities:
        target = ent["text"]
        target_lower = target.lower()
        idx = text_lower.find(target_lower)
        if idx == -1:
            raise ValueError(f"Entity '{target}' not found in text: '{text}'")

        start = idx
        end = idx + len(target)
        # Double check exact slice
        assert text[start:end].lower() == target_lower

        spans.append(
            {
                "start": start,
                "end": end,
                "entity": ent["entity"],
                "text": text[start:end],
                "negated": ent.get("negated", False),
            }
        )

    # Sort spans by start index
    spans.sort(key=lambda s: s["start"])
    return spans


def generate_seed_records(
    num_dogs: int = 25,
    records_per_dog_range: tuple[int, int] = (1, 3),
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Generate a synthetic veterinary dataset ensuring multiple observations per dog.

    Returns a list of dicts with keys:
      - `record_id`: unique identifier
      - `pet_id`: dog identifier (e.g. 'dog_001')
      - `text`: clinical description
      - `condition_label`: standard 4-class label
      - `spans`: character-level entity offsets
      - `is_emergency`: boolean triage flag
    """
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    record_counter = 1

    for dog_idx in range(1, num_dogs + 1):
        pet_id = f"dog_{dog_idx:03d}"
        n_obs = rng.randint(records_per_dog_range[0], records_per_dog_range[1])

        # Pick primary condition predisposition for this dog
        dog_condition = rng.choice(CONDITION_CATEGORIES)
        available_templates = RAW_TEMPLATES[dog_condition]

        for _ in range(n_obs):
            tmpl = rng.choice(available_templates)
            spans = compute_spans(tmpl["text"], tmpl["entities"])

            record = {
                "record_id": f"rec_{record_counter:04d}",
                "pet_id": pet_id,
                "text": tmpl["text"],
                "condition_label": dog_condition,
                "spans": spans,
                "is_emergency": tmpl.get("is_emergency", False),
            }
            records.append(record)
            record_counter += 1

    return records


def export_seed_dataset(output_path: str | Path, records: list[dict[str, Any]]) -> None:
    """Export records to JSONL file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(rec) + "\n" for rec in records)


def load_seed_dataset(input_path: str | Path) -> list[dict[str, Any]]:
    """Load records from JSONL file."""
    path = Path(input_path)
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate veterinary NLP seed dataset")
    parser.add_argument("--out", type=str, default="data/seed_symptoms.jsonl")
    parser.add_argument("--num-dogs", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    generated = generate_seed_records(num_dogs=args.num_dogs, seed=args.seed)
    export_seed_dataset(args.out, generated)
    print(f"Generated {len(generated)} symptom records across {args.num_dogs} dogs -> {args.out}")
