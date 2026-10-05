# 04: Offline Multi-Task Training Pipeline (ml/nlp)

**What to build:** The complete offline machine learning training, evaluation, and dataset workspace in `ml/nlp/`. Defines the multi-task PyTorch model architecture (`MultiTaskSymptomTransformer`) based on `distilbert-base-uncased` featuring a token-classification head for BIO entity spans and a sequence-classification head for 4-class condition probabilities (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`). Implements dataset token alignment with dog-level data splitting (`ml.common.data_splitting`), a synthetic `seed_data.py` generator for immediate pipeline verification, a multi-task training loop (`train.py`), and an evaluation module (`evaluate.py`) calculating Macro-F1, Accuracy, and ECE calibration error, exporting checkpoints into `model_registry/nlp/`.

**Blocked by:** 01: Core Clean Architecture Scaffolding and Stub API Endpoint

**Status:** ready-for-agent

## Acceptance Criteria

- [ ] `ml/nlp/model.py` defines `MultiTaskSymptomTransformer` with a shared Transformer encoder and dual heads for token NER and sequence classification.
- [ ] `ml/nlp/dataset.py` aligns token spans with subword tokenizers and integrates `dog_level_train_val_test_split` to avoid animal data leakage.
- [ ] `ml/nlp/seed_data.py` generates a rich, realistic veterinary seed dataset (JSONL) covering diverse symptoms, body parts, durations, and conditions.
- [ ] `ml/nlp/train.py` trains the multi-task model with joint weighted loss ($\alpha=0.6 \cdot \text{Loss}_{\text{NER}} + 0.4 \cdot \text{Loss}_{\text{condition}}$) and exports checkpoints to `model_registry/nlp/`.
- [ ] `ml/nlp/evaluate.py` computes span Macro/Micro F1, condition Macro-F1, Accuracy, and Expected Calibration Error (ECE from `ml.common.metrics`).
- [ ] Unit tests verify model forward pass shapes, seed dataset generation, and loss calculation.
