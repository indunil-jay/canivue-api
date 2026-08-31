# NLP (Symptom) Model

Fine-tunes a compact Transformer (lightweight BERT/RoBERTa variant) on
veterinarian-annotated owner symptom descriptions to do (1) information
extraction (symptom category, body location, duration, severity cues) and
(2) condition classification (proposal §5.7.3). Serves a future
`app/features/symptom_nlp/infrastructure/ml/engine.py`.

- **Two related tasks, one checkpoint or two**: extraction can be framed as
  token classification (NER-style) and condition classification as sequence
  classification. Whether they share a backbone with two heads or are two
  fine-tuned models is an open design choice — document whichever is chosen
  in `train.py`'s docstring once implemented.
- **Text-quality scoring** (description length, symptom-term count,
  presence of body-location/duration/severity info) is a plain heuristic,
  not a trained model — it belongs in the serving-side
  `infrastructure/ml/preprocessing.py` once that feature exists (see
  `.agents/skills/ml-feature/SKILL.md`), not here.
- **Data**: 1,000–3,000 labelled symptom records (proposal Table 4), mapped
  to a standardized symptom-category ontology — not committed to the repo.

## Usage (once real data is wired in)

```bash
pip install -r requirements-ml.txt   # from repo root
python -m ml.nlp.train --data-dir /path/to/symptom_records --epochs 5 \
    --out model_registry/nlp/symptom_bert_v1
```

## Model versions

| Version | Trained on | Notes |
|---|---|---|
| _(none yet)_ | — | Follow `ml/vision/train.py` as the worked reference for this training loop's shape. |
