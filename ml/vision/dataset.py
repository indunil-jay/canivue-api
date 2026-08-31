"""Dataset loading for the visual condition classifier.

Requires `requirements-ml.txt` (torch, torchvision, Pillow).
"""

import csv
from pathlib import Path
from typing import List, Tuple

# Keep in sync with SUPPORTED_CONDITIONS in the future
# app/features/vision_diagnosis/infrastructure/ml/engine.py serving engine.
LABELS: List[str] = [
    "healthy",
    "skin_abnormality",
    "eye_condition",
    "ear_inflammation",
    "open_wound",
]
LABEL_TO_INDEX = {label: i for i, label in enumerate(LABELS)}


class CanineVisionDataset:
    """Expects a directory of images plus a `labels.csv` with columns:
    `image_path,pet_id,label,quality_note` (quality_note is optional, human QA notes).

    `pet_id` is required (not just for training) so `ml/common/data_splitting.py`
    can split at the dog level and avoid leaking the same dog's photos across
    train/val/test.
    """

    def __init__(self, data_dir: str, records: List[dict], image_size: int = 224):
        import torchvision.transforms as T

        self.data_dir = Path(data_dir)
        self.records = records
        self.transform = T.Compose(
            [
                T.Resize((image_size, image_size)),
                T.RandomHorizontalFlip(),
                T.ColorJitter(brightness=0.2, contrast=0.2),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple["torch.Tensor", int]:  # noqa: F821
        from PIL import Image

        record = self.records[idx]
        image = Image.open(self.data_dir / record["image_path"]).convert("RGB")
        tensor = self.transform(image)
        label_idx = LABEL_TO_INDEX[record["label"]]
        return tensor, label_idx


def load_labels_csv(labels_csv_path: str) -> List[dict]:
    """Read `labels.csv` into a list of record dicts for splitting/loading."""
    with open(labels_csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
