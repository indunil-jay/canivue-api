"""Canivue AI — NLP Clinical Inspector & Active Learning Studio Backend.

Provides interactive model visualization, decision brain inspection, and human-in-the-loop
feedback recording to continuously enhance model accuracy and fine-tuning datasets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ml.nlp.pipeline import SymptomParserPipeline

app = FastAPI(
    title="Canivue AI — NLP Clinical Inspector & Active Learning Studio",
    description="Interactive model inspection, decision reasoning, and HITL feedback loop",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared pipeline instance
PIPELINE = SymptomParserPipeline()
DATA_DIR = Path("data")
FEEDBACK_FILE = DATA_DIR / "active_learning_feedback.jsonl"


class ParseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw canine symptom text")


class FeedbackSample(BaseModel):
    text: str
    condition_label: str
    symptoms: list[str] = Field(default_factory=list)
    spans: list[dict[str, Any]] = Field(default_factory=list)
    is_emergency: bool = False
    pet_id: str = "dog_annotated_hitl"
    feedback_notes: str | None = None


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the single-page interactive UI."""
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="UI index.html not found.")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/parse")
async def parse_symptom_text(req: ParseRequest) -> dict[str, Any]:
    """Execute model inference and return clinical decision brain breakdown."""
    try:
        result = PIPELINE.predict(req.text)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Generate decision reasoning explanation for the inspector
    reasoning: list[str] = []
    probs = result["condition_probabilities"]
    top_cond = max(probs, key=probs.get) if probs else "other"
    top_prob = probs.get(top_cond, 0.0)

    if result["emergency_triage"]["is_critical"]:
        reasoning.append(
            f"🚨 EMERGENCY ALERT: Triggered by keyword '{result['emergency_triage']['reason']}'. "
            f"Recommendation: {result['emergency_triage']['recommendation']}"
        )
    else:
        reasoning.append("✅ Clinical Safety: No acute life-threatening emergency flags detected.")

    if result["negated_symptoms"]:
        reasoning.append(
            f"🚫 Negation Scoping: Excluded negated symptoms {result['negated_symptoms']} from "
            f"condition probability calculation to prevent false-positive inflation."
        )

    if result["symptoms"]:
        reasoning.append(
            f"🔍 Primary Symptoms: Extracted {result['symptoms']} mapped to {top_cond} "
            f"with confidence {top_prob:.1%}."
        )

    if result["duration"]:
        dur = result["duration"]
        reasoning.append(
            f"⏱️ Temporal Metric: Duration normalized to {dur['value']} {dur['unit']}."
        )

    if result["progression"]:
        reasoning.append(
            f"📈 Progression Trajectory: Evaluated as '{result['progression']}' based on clinical cues."
        )

    reasoning.append(
        f"📊 Multimodal Weight: Text quality score {result['text_quality_score']:.2f} combined with "
        f"model confidence {result['model_confidence']:.2f} yields modality reliability {result['modality_reliability_score']:.2f}."
    )

    return {
        "success": True,
        "data": result,
        "decision_reasoning": reasoning,
    }


@app.post("/api/feedback")
def submit_human_feedback(sample: FeedbackSample) -> dict[str, Any]:
    """Record human-verified corrections to enhance model accuracy in active learning loop."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "record_id": f"hitl_{Path(FEEDBACK_FILE).stat().st_size if FEEDBACK_FILE.exists() else 0}",
        "pet_id": sample.pet_id,
        "text": sample.text,
        "condition_label": sample.condition_label,
        "spans": sample.spans,
        "symptoms": sample.symptoms,
        "is_emergency": sample.is_emergency,
        "feedback_notes": sample.feedback_notes,
    }

    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    # Count total feedback samples
    total_samples = 0
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        total_samples = sum(1 for line in f if line.strip())

    return {
        "success": True,
        "message": "Human verification recorded into active learning training pool.",
        "total_feedback_samples": total_samples,
    }


@app.get("/api/feedback/stats")
def get_feedback_stats() -> dict[str, Any]:
    """Return active learning feedback statistics."""
    total_samples = 0
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            total_samples = sum(1 for line in f if line.strip())

    return {
        "total_feedback_samples": total_samples,
        "feedback_file": str(FEEDBACK_FILE),
    }


@app.get("/api/scenarios")
def get_benchmark_scenarios() -> list[dict[str, Any]]:
    """Return pre-built clinical benchmark scenarios."""
    return [
        {
            "id": "ear_inflammation_bilateral",
            "title": "Bilateral Ear Inflammation",
            "description": "Owner reports classic bilateral scratching with shaking.",
            "text": "My golden retriever has been scratching both ears and shaking his head constantly for 4 days.",
        },
        {
            "id": "skin_allergy_with_negation",
            "title": "Allergic Dermatitis with Negation",
            "description": "Tests negation scoping; owner clarifies no vomiting.",
            "text": "He has intense itching and red hair loss on his belly for a week, but no vomiting and not coughing.",
        },
        {
            "id": "corneal_ocular_discharge",
            "title": "Unilateral Eye Discharge & Worsening",
            "description": "Tests progression cue and eye location.",
            "text": "Watery discharge from right eye since yesterday morning, definitely getting worse.",
        },
        {
            "id": "acute_emergency_collapse",
            "title": "Acute Life-Threatening Emergency",
            "description": "Triggers emergency triage red-flag guardrail.",
            "text": "Emergency: My dog suddenly collapsed in the yard, gums look pale blue and he is gasping for air!",
        },
        {
            "id": "vague_insufficient_text",
            "title": "Vague / Low Quality Description",
            "description": "Tests quality scoring penalty and warnings.",
            "text": "My dog seems a bit off today.",
        },
    ]


if __name__ == "__main__":
    import uvicorn

    print("Launching Canivue NLP Clinical Inspector on http://localhost:8050")
    uvicorn.run("tools.nlp_inspector.app:app", host="127.0.0.1", port=8050, reload=True)
