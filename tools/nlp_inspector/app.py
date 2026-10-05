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
from tools.nlp_inspector.chat_service import (
    create_new_session,
    delete_session_by_id,
    get_session_by_id,
    load_all_sessions,
    process_user_chat_message,
)

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


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message text")


class CreateChatRequest(BaseModel):
    title: str | None = None


class FeedbackSample(BaseModel):
    text: str
    condition_label: str
    symptoms: list[str] = Field(default_factory=list)
    spans: list[dict[str, Any]] = Field(default_factory=list)
    is_emergency: bool = False
    pet_id: str = "dog_annotated_hitl"
    feedback_notes: str | None = None


@app.get("/api/chats")
def list_chats() -> list[dict[str, Any]]:
    """List all saved chat sessions."""
    sessions = load_all_sessions()
    return [
        {
            "id": s["id"],
            "title": s.get("title", "Consultation"),
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
            "message_count": len(s.get("messages", [])),
            "last_condition": s.get("accumulated_context", {}).get("last_condition"),
            "emergency": s.get("accumulated_context", {}).get("emergency", False),
        }
        for s in sessions
    ]


@app.post("/api/chats")
def create_chat(req: CreateChatRequest | None = None) -> dict[str, Any]:
    """Create a new chat session."""
    title = req.title if req else None
    return create_new_session(initial_title=title)


@app.get("/api/chats/{chat_id}")
def get_chat(chat_id: str) -> dict[str, Any]:
    """Get full chat session with all messages."""
    session = get_session_by_id(chat_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@app.post("/api/chats/{chat_id}/messages")
def send_chat_message(chat_id: str, req: ChatMessageRequest) -> dict[str, Any]:
    """Send a message to a chat session, run reasoning and assumptions, and return assistant reply."""
    try:
        return process_user_chat_message(
            session_id=chat_id,
            user_text=req.message,
            pipeline=PIPELINE,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str) -> dict[str, Any]:
    """Delete a chat session."""
    deleted = delete_session_by_id(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"success": True, "message": "Chat session deleted"}


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


@app.get("/api/evaluate")
def evaluate_dataset() -> dict[str, Any]:
    """Dynamically evaluate the current NLP AI engine across all benchmark samples and active learning pool."""
    records: list[dict[str, Any]] = []
    seed_file = DATA_DIR / "seed_symptoms.jsonl"
    if seed_file.exists():
        with open(seed_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

    feedback_records = []
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    feedback_records.append(r)
                    records.append(r)

    if not records:
        return {
            "success": False,
            "message": "No evaluation records found in data/seed_symptoms.jsonl",
        }

    total = len(records)
    correct = 0
    by_cond: dict[str, dict[str, Any]] = {}
    misclassified: list[dict[str, Any]] = []

    for r in records:
        gt = r.get("condition_label", "other")
        if gt not in by_cond:
            by_cond[gt] = {"total": 0, "correct": 0, "accuracy": 0.0}
        by_cond[gt]["total"] += 1

        pred_res = PIPELINE.predict(r["text"])
        probs = pred_res["condition_probabilities"]
        pred = max(probs, key=probs.get) if probs else "other"

        if pred == gt:
            correct += 1
            by_cond[gt]["correct"] += 1
        else:
            misclassified.append({
                "record_id": r.get("record_id", "seed"),
                "text": r["text"],
                "ground_truth": gt,
                "predicted": pred,
                "confidence": probs.get(pred, 0.0),
                "probabilities": probs,
                "emergency": pred_res.get("emergency_triage", {}).get("is_critical", False),
            })

    for v in by_cond.values():
        v["accuracy"] = round(v["correct"] / v["total"], 4) if v["total"] > 0 else 0.0

    overall_acc = round(correct / total, 4) if total > 0 else 0.0

    return {
        "success": True,
        "overall_accuracy": overall_acc,
        "overall_accuracy_percent": f"{overall_acc * 100:.1f}%",
        "total_samples": total,
        "correct_count": correct,
        "misclassified_count": len(misclassified),
        "feedback_samples_count": len(feedback_records),
        "by_condition": by_cond,
        "misclassified_samples": misclassified,
        "model_version": PIPELINE.model_version,
    }


@app.post("/api/train")
def train_model() -> dict[str, Any]:
    """Execute active learning consolidation and trigger training if torch is present."""
    feedback_count = 0
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_count = sum(1 for line in f if line.strip())

    torch_available = False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        torch_available = True
    except ImportError:
        torch_available = False

    if torch_available:
        from ml.nlp.train import train_multitask_nlp
        history = train_multitask_nlp(
            data_path=str(FEEDBACK_FILE) if feedback_count >= 10 else "data/seed_symptoms.jsonl",
            epochs=2,
            out_dir="model_registry/nlp/symptom_distilbert_v1",
        )
        return {
            "success": True,
            "mode": "neural_fine_tuning",
            "message": "Fine-tuning completed successfully using Multi-Task DistilBERT!",
            "feedback_samples_used": feedback_count,
            "training_history": history,
        }
    else:
        return {
            "success": True,
            "mode": "active_learning_pool_ready",
            "message": f"Active learning feedback pool consolidated with {feedback_count} verified samples.",
            "feedback_samples_count": feedback_count,
            "command": f"python -m ml.nlp.train --data-path {FEEDBACK_FILE if feedback_count > 0 else 'data/seed_symptoms.jsonl'}",
            "hint": "PyTorch is not installed in the lightweight runtime. Verified samples are saved in data/active_learning_feedback.jsonl ready for offline fine-tuning.",
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
