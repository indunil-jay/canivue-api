"""Model architecture definitions for canine ear disease classification.

Provides the transfer learning backbone (EfficientNet-B0) fine-tuned for
Canivue's 4-class canine ear conditions.
"""

from typing import Optional

from ml.ear.dataset import LABELS


def build_model(num_classes: Optional[int] = None, pretrained: bool = True):
    """Build an EfficientNet-B0 model with a custom linear classification head.

    Args:
        num_classes: Number of target condition classes. Defaults to len(LABELS) (4 classes).
        pretrained: Whether to load ImageNet pretrained weights ('IMAGENET1K_V1').
                   Can be set to False for unit tests or offline initialization.

    Returns:
        torch.nn.Module: Configured EfficientNet-B0 neural network.
    """
    import torch
    from torchvision import models

    if num_classes is None:
        num_classes = len(LABELS)

    weights = "IMAGENET1K_V1" if pretrained else None
    model = models.efficientnet_b0(weights=weights)

    in_features = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(in_features, num_classes)
    return model


def freeze_backbone(model: "torch.nn.Module") -> None:
    """Freeze all backbone feature layers for Stage A training.

    Leaves only the final linear classifier trainable.
    """
    for param in model.features.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True


def unfreeze_top_blocks(model: "torch.nn.Module", num_stages: int = 2) -> None:
    """Unfreeze the top `num_stages` feature blocks for Stage B fine-tuning.

    EfficientNet-B0 contains 9 sequential stages in `model.features` (0..8).
    Unfreezing the final stages (by default stages 7 and 8) allows high-level
    semantic adaptation to canine ear canal and pinna lesions while retaining
    foundational edge and texture detectors frozen.
    """
    total_stages = len(model.features)
    unfreeze_from = max(0, total_stages - num_stages)

    for i, stage in enumerate(model.features):
        requires_grad = i >= unfreeze_from
        for param in stage.parameters():
            param.requires_grad = requires_grad

    for param in model.classifier.parameters():
        param.requires_grad = True
