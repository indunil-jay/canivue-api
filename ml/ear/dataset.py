"""Dataset loading and transformation pipelines for canine ear disease classification.

Defines the 4-class ear condition taxonomy, deterministic and augmented
torchvision transformation pipelines, manifest parsing, and the PyTorch Dataset.
"""

import csv
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

# Four ear-condition classes; each must match a dataset sub-folder name exactly.
# EDIT THIS LIST (and EXPECTED_CLASSES in prepare_dataset.py) if your dataset
# uses different class folder names.
# Kept in sync with the future ear-diagnosis serving engine under app/features/.
LABELS: List[str] = [
    "Bacterial_otitis",
    "Ear_mites",
    "Fungal_otitis",
    "Healthy",
]

LABEL_TO_INDEX: Dict[str, int] = {label: i for i, label in enumerate(LABELS)}
INDEX_TO_LABEL: Dict[int, str] = {i: label for i, label in enumerate(LABELS)}

# Standard ImageNet normalization parameters matching EfficientNet pretraining.
IMAGENET_MEAN: List[float] = [0.485, 0.456, 0.406]
IMAGENET_STD: List[float] = [0.229, 0.224, 0.225]


def get_train_transforms(image_size: int = 224) -> Callable:
    """Training transformations with data augmentation.

    Applies resizing to (image_size, image_size), random horizontal flip,
    mild color jitter (brightness and contrast), conversion to tensor,
    and ImageNet normalization.
    """
    import torchvision.transforms as T

    return T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.RandomHorizontalFlip(p=0.5),
            T.ColorJitter(brightness=0.2, contrast=0.2),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def get_eval_transforms(image_size: int = 224) -> Callable:
    """Validation and testing transformations.

    Applies deterministic resizing to (image_size, image_size), conversion to tensor,
    and ImageNet normalization without any stochastic operations.
    Guarantees deterministic metric evaluation.
    """
    import torchvision.transforms as T

    return T.Compose(
        [
            T.Resize((image_size, image_size)),
            T.ToTensor(),
            T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


class CanineEarDataset:
    """PyTorch Dataset for canine ear disease condition classification.

    Expects a dataset root `data_dir` and a list of `records` loaded from `labels.csv`
    containing keys `image_path` (relative to `data_dir`), `pet_id`, and `label`.

    Supports an externally supplied `transform` callable. If not provided,
    defaults to the deterministic evaluation transform (`get_eval_transforms()`).
    """

    def __init__(
        self,
        data_dir: Union[str, Path],
        records: List[dict],
        transform: Optional[Callable] = None,
        image_size: int = 224,
    ):
        self.data_dir = Path(data_dir)
        self.records = records
        self.image_size = image_size
        self.transform = transform if transform is not None else get_eval_transforms(image_size)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple["torch.Tensor", int]:  # noqa: F821
        from PIL import Image

        record = self.records[idx]
        image_path_str = record.get("image_path")
        if not image_path_str:
            raise ValueError(f"Record at index {idx} is missing 'image_path': {record}")

        img_file = self.data_dir / image_path_str
        if not img_file.exists():
            raise FileNotFoundError(
                f"Image file not found at: {img_file} (relative path: '{image_path_str}')"
            )

        label_name = record.get("label")
        if label_name not in LABEL_TO_INDEX:
            raise ValueError(
                f"Invalid or unrecognized label '{label_name}' at index {idx}. "
                f"Expected one of: {list(LABEL_TO_INDEX.keys())}"
            )

        try:
            image = Image.open(img_file).convert("RGB")
        except Exception as exc:
            raise OSError(f"Failed to open or decode image at {img_file}: {exc}") from exc

        tensor = self.transform(image)
        label_idx = LABEL_TO_INDEX[label_name]
        return tensor, label_idx


def load_labels_csv(labels_csv_path: Union[str, Path]) -> List[dict]:
    """Read `labels.csv` into a list of validated record dicts.

    Ensures that required columns ('image_path', 'label') are present, that no
    row is empty, and that labels correspond to the recognized taxonomy.
    Does not drop invalid rows silently; raises clear exceptions instead.
    """
    path = Path(labels_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Labels manifest not found at: {path}")

    records: List[dict] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_fields = {"image_path", "label"}
        fieldnames = set(reader.fieldnames or [])

        if not required_fields.issubset(fieldnames):
            raise ValueError(
                f"Labels CSV manifest at {path} is missing required columns. "
                f"Found {list(fieldnames)}, required {list(required_fields)}"
            )

        for line_num, row in enumerate(reader, start=2):
            img_path = (row.get("image_path") or "").strip()
            label = (row.get("label") or "").strip()

            if not img_path:
                raise ValueError(
                    f"Invalid record at line {line_num} in {path}: 'image_path' is empty."
                )
            if not label:
                raise ValueError(
                    f"Invalid record at line {line_num} in {path}: 'label' is empty."
                )
            if label not in LABEL_TO_INDEX:
                raise ValueError(
                    f"Invalid label '{label}' at line {line_num} in {path}. "
                    f"Must be one of: {list(LABEL_TO_INDEX.keys())}"
                )

            records.append(dict(row))

    return records
