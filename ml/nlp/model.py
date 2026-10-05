"""Multi-Task Transformer architecture for joint symptom entity extraction and condition classification.

Architecture (ADR 0002):
- Shared Transformer backbone (e.g. distilbert-base-uncased)
- Token classification head for BIO symptom entity recognition
- Sequence classification head for 4-class canine condition probabilities
- Weighted multi-task loss: Loss = alpha * Loss_NER + beta * Loss_condition (default 0.6 / 0.4)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ml.nlp.dataset import CONDITION_LABELS, NER_LABELS


class MultiTaskSymptomTransformer:
    """Wrapper / module for Multi-Task DistilBERT."""

    def __init__(
        self,
        base_model_name: str = "distilbert-base-uncased",
        num_ner_labels: int = len(NER_LABELS),
        num_conditions: int = len(CONDITION_LABELS),
        dropout_prob: float = 0.2,
    ):
        self.base_model_name = base_model_name
        self.num_ner_labels = num_ner_labels
        self.num_conditions = num_conditions
        self.dropout_prob = dropout_prob

        # Lazily initialize PyTorch module
        self._torch_module = None

    def _ensure_module(self):
        if self._torch_module is None:
            from torch import nn
            from transformers import AutoConfig, AutoModel

            class _PyTorchMultiTaskModel(nn.Module):
                def __init__(
                    self,
                    model_name: str,
                    num_ner: int,
                    num_cond: int,
                    dropout: float,
                ):
                    super().__init__()
                    self.config = AutoConfig.from_pretrained(model_name)
                    self.encoder = AutoModel.from_pretrained(model_name, config=self.config)
                    hidden_size = self.config.hidden_size

                    self.dropout = nn.Dropout(dropout)
                    self.ner_head = nn.Linear(hidden_size, num_ner)
                    self.condition_head = nn.Linear(hidden_size, num_cond)

                def forward(
                    self,
                    input_ids,
                    attention_mask=None,
                    ner_labels=None,
                    condition_label=None,
                    alpha: float = 0.6,
                    beta: float = 0.4,
                ):
                    outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
                    sequence_output = outputs[0]  # [batch_size, seq_len, hidden_size]

                    # Token classification (NER)
                    ner_logits = self.ner_head(self.dropout(sequence_output))

                    # Sequence classification ([CLS] token or pooled)
                    cls_representation = sequence_output[:, 0, :]
                    condition_logits = self.condition_head(self.dropout(cls_representation))

                    loss = None
                    if ner_labels is not None and condition_label is not None:
                        loss_fct_ner = nn.CrossEntropyLoss(ignore_index=-100)
                        loss_fct_cond = nn.CrossEntropyLoss()

                        loss_ner = loss_fct_ner(
                            ner_logits.view(-1, ner_logits.shape[-1]),
                            ner_labels.view(-1),
                        )
                        loss_cond = loss_fct_cond(
                            condition_logits.view(-1, condition_logits.shape[-1]),
                            condition_label.view(-1),
                        )
                        loss = (alpha * loss_ner) + (beta * loss_cond)

                    return {
                        "loss": loss,
                        "ner_logits": ner_logits,
                        "condition_logits": condition_logits,
                    }

            self._torch_module = _PyTorchMultiTaskModel(
                self.base_model_name,
                self.num_ner_labels,
                self.num_conditions,
                self.dropout_prob,
            )
        return self._torch_module

    def to(self, device: Any):
        module = self._ensure_module()
        return module.to(device)

    def __call__(self, *args, **kwargs):
        module = self._ensure_module()
        return module(*args, **kwargs)

    def parameters(self):
        module = self._ensure_module()
        return module.parameters()

    def train(self, mode: bool = True):
        module = self._ensure_module()
        module.train(mode)

    def eval(self):
        module = self._ensure_module()
        module.eval()

    def save_pretrained(self, save_directory: str | Path) -> None:
        """Save model checkpoint, configuration, and label mappings."""
        import torch

        save_dir = Path(save_directory)
        save_dir.mkdir(parents=True, exist_ok=True)

        module = self._ensure_module()
        torch.save(module.state_dict(), save_dir / "pytorch_model.bin")

        metadata = {
            "base_model_name": self.base_model_name,
            "num_ner_labels": self.num_ner_labels,
            "num_conditions": self.num_conditions,
            "dropout_prob": self.dropout_prob,
            "ner_labels": NER_LABELS,
            "condition_labels": CONDITION_LABELS,
        }
        with open(save_dir / "canivue_nlp_config.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def from_pretrained(cls, load_directory: str | Path) -> MultiTaskSymptomTransformer:
        """Load model checkpoint from directory."""
        import torch

        load_dir = Path(load_directory)
        with open(load_dir / "canivue_nlp_config.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)

        instance = cls(
            base_model_name=metadata["base_model_name"],
            num_ner_labels=metadata["num_ner_labels"],
            num_conditions=metadata["num_conditions"],
            dropout_prob=metadata.get("dropout_prob", 0.2),
        )

        module = instance._ensure_module()
        state_dict = torch.load(load_dir / "pytorch_model.bin", map_location="cpu")
        module.load_state_dict(state_dict)
        return instance
