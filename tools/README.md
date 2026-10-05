# Canivue AI — Developer & Clinical Tools

This directory contains standalone developer, research, and clinical inspection tools for exploring and enhancing Canivue AI's intelligence models.

---

## 🔬 NLP Clinical Inspector & Active Learning Studio (`tools/nlp_inspector/`)

An interactive visualizer and Human-in-the-Loop (HITL) studio for inspecting the **Canine Symptom NLP Decision Brain** and continuously collecting ground-truth feedback to enhance model accuracy.

### Features
1. **Interactive Clinical Entity Highlighting**: Visualizes exact character-level span offsets for symptoms, body locations with laterality (`left`, `right`), durations, frequencies, and progression cues directly over the owner's raw description.
2. **Emergency Triage Monitor**: Real-time evaluation of acute clinical red-flags (collapse, respiratory distress, cyanosis, acute seizures, GDV, severe trauma).
3. **Calibrated Condition Probabilities**: Visual bar charts across the 4 canonical categories (`ear_inflammation`, `skin_condition`, `eye_condition`, `other`).
4. **Transparent Decision Brain Audit Trail**: Plain-language step-by-step reasoning explaining how the AI parsed the text and weighted each piece of evidence.
5. **Vice-Versa Model Accuracy Enhancement (HITL Feedback Loop)**:
   - Clinicians or engineers can inspect any prediction.
   - If the model misclassifies a condition or misses an entity, select the verified label and click **"Save Verified Sample to Training Pool"**.
   - Verified records are stored into `data/active_learning_feedback.jsonl` in the standard schema consumed by `ml/nlp/train.py`.
   - Re-running `python -m ml.nlp.train --data-path data/active_learning_feedback.jsonl` continuously improves the neural model's weights and decision brain!

---

### Quick Start

Launch with a single command:

```bash
python tools/nlp_inspector/run.py
```

Then open your browser at **`http://localhost:8050`** (opens automatically).

Alternatively, you can double-click **`tools/nlp_inspector/index.html`** in any web browser to explore benchmark clinical scenarios in standalone mode.
