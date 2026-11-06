"""Dataset manifest generator for canine ear disease classification.

Scans the canine ear disease image dataset directory, verifies image integrity
via Pillow, filters out non-image files, and generates a standardized `labels.csv`
manifest ready for consumption by Canivue's ear pipeline.

Usage:
    python -m ml.ear.prepare_dataset --data-dir "C:/final_project/dataset keggle/Dogs ear diseases"

Or with custom output:
    python -m ml.ear.prepare_dataset \
        --data-dir "C:/final_project/dataset keggle/Dogs ear diseases" \
        --out "C:/final_project/dataset keggle/Dogs ear diseases/labels.csv"
"""

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Exact four classes present in the canine ear disease image dataset.
EXPECTED_CLASSES: List[str] = [
    "Bacterial_otitis",
    "Ear_mites",
    "Fungal_otitis",
    "Healthy",
]

# Supported image file extensions.
VALID_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}


def verify_image(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Verify that a file can be opened and decoded as a valid image using Pillow.

    Returns:
        (True, None) if the image is valid.
        (False, error_message) if the image is corrupted or cannot be read.
    """
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as e:
        raise RuntimeError(
            "Pillow is required for image verification. "
            "Please install requirements-ml.txt or Pillow: pip install Pillow"
        ) from e

    try:
        # First pass: verify header and image integrity
        with Image.open(file_path) as img:
            img.verify()

        # Second pass: ensure actual pixel payload can be decompressed/loaded
        with Image.open(file_path) as img:
            img.load()

        return True, None
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        return False, str(exc)
    except Exception as exc:  # Catch-all for unexpected image decoding faults
        return False, f"Unexpected error during decoding: {exc}"


def scan_and_generate_manifest(
    data_dir: Path,
    out_csv: Path,
    verify: bool = True,
) -> Dict[str, object]:
    """Scan the dataset directory and write `labels.csv`.

    Args:
        data_dir: Root directory of the dataset containing class folders.
        out_csv: Target path for the output `labels.csv` manifest.
        verify: Whether to perform deep verification of image integrity with Pillow.

    Returns:
        A dictionary containing scan summary metrics.
    """
    if not data_dir.exists() or not data_dir.is_dir():
        raise FileNotFoundError(f"Dataset root directory does not exist: {data_dir}")

    records: List[Dict[str, str]] = []
    class_counts: Dict[str, int] = {cls_name: 0 for cls_name in EXPECTED_CLASSES}
    ignored_files: List[Tuple[str, str]] = []  # (rel_path, reason)
    corrupted_files: List[Tuple[str, str]] = []  # (rel_path, error_message)

    print(f"Scanning dataset directory: {data_dir.resolve()}")

    for class_name in EXPECTED_CLASSES:
        class_folder = data_dir / class_name
        if not class_folder.exists() or not class_folder.is_dir():
            print(f"[WARNING] Expected class directory not found: {class_folder}")
            continue

        # Sort files for deterministic ordering across runs and platforms
        for file_path in sorted(class_folder.iterdir()):
            if file_path.is_dir():
                # If there are subdirectories, scan them recursively
                sub_files = sorted(file_path.rglob("*"))
            else:
                sub_files = [file_path]

            for item in sub_files:
                if not item.is_file():
                    continue

                rel_path = item.relative_to(data_dir).as_posix()
                ext = item.suffix.lower()

                # Filter out non-image files (e.g. desktop.ini, .DS_Store, .gitkeep)
                if ext not in VALID_IMAGE_EXTENSIONS:
                    ignored_files.append((rel_path, f"Unsupported extension '{ext}'"))
                    continue

                # Verify image integrity via Pillow
                if verify:
                    is_valid, error_msg = verify_image(item)
                    if not is_valid:
                        corrupted_files.append((rel_path, error_msg or "Unknown corruption"))
                        continue

                # Fallback Pet ID:
                # The ear dataset is assumed not to provide individual dog IDs (subject tracking).
                # To satisfy `CanineEarDataset` and `ml/common/data_splitting.py` without
                # falsely implying biological dog identities, we use a distinct, transparent
                # image-level fallback ID: "img_fallback_<class>_<index:04d>".
                # When splitting, each photo will be treated as an independent observation.
                class_counts[class_name] += 1
                fallback_pet_id = f"img_fallback_{class_name}_{class_counts[class_name]:04d}"

                records.append({
                    "image_path": rel_path,
                    "pet_id": fallback_pet_id,
                    "label": class_name,
                })

    # Ensure destination directory exists
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # Write labels.csv
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "pet_id", "label"])
        writer.writeheader()
        writer.writerows(records)

    total_valid = len(records)

    return {
        "out_csv": out_csv.resolve(),
        "total_valid": total_valid,
        "class_counts": class_counts,
        "ignored_files": ignored_files,
        "corrupted_files": corrupted_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan canine ear disease dataset and generate a clean labels.csv manifest."
    )
    parser.add_argument(
        "--data-dir",
        required=True,
        type=str,
        help="Root path of the dataset (e.g. 'C:/final_project/dataset keggle/Dogs ear diseases')",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output CSV path. Defaults to '<data-dir>/labels.csv' (outside Git repository).",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip deep image verification via Pillow (not recommended).",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_csv = Path(args.out).resolve() if args.out else data_dir / "labels.csv"

    print("=" * 60)
    print("Canivue Ear - Dataset Manifest Generator")
    print("=" * 60)

    results = scan_and_generate_manifest(
        data_dir=data_dir,
        out_csv=out_csv,
        verify=not args.skip_verify,
    )

    print("\n--- Scan Results ---")
    for cls_name, count in results["class_counts"].items():
        print(f"  - {cls_name:38s}: {count:4d} images")
    print(f"  Total Valid Images: {results['total_valid']:4d}")

    ignored = results["ignored_files"]
    if ignored:
        print(f"\n--- Ignored Files ({len(ignored)}) ---")
        for rel_path, reason in ignored:
            print(f"  [IGNORED] {rel_path} ({reason})")

    corrupted = results["corrupted_files"]
    if corrupted:
        print(f"\n--- Corrupted / Unreadable Images ({len(corrupted)}) ---")
        for rel_path, error in corrupted:
            print(f"  [CORRUPTED] {rel_path}: {error}")
    else:
        print("\nAll verified images are valid and uncorrupted.")

    print(f"\nManifest successfully written to:\n  {results['out_csv']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

