"""Canivue AI — Chat Service with Multi-Turn Conversational Reasoning.

Handles session persistence, multi-turn clinical context tracking,
explicit model assumption derivation, and conversational decision explanations.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.features.symptom_nlp.domain.entities import (
    BodyLocation,
    DurationEntity,
    EmergencyTriageAlert,
    ExtractedSpan,
    SymptomParseResult,
)
from app.features.symptom_nlp.domain.intake_rules import (
    evaluate_missing_slots,
    generate_clarifying_prompt,
)
from ml.nlp.pipeline import SymptomParserPipeline

SESSIONS_FILE = Path("data/chat_sessions.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_all_sessions() -> list[dict[str, Any]]:
    """Load all chat sessions from disk."""
    if not SESSIONS_FILE.exists():
        return []
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def save_all_sessions(sessions: list[dict[str, Any]]) -> None:
    """Save all chat sessions to disk."""
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


def get_session_by_id(session_id: str) -> dict[str, Any] | None:
    """Retrieve a single session by its unique ID."""
    sessions = load_all_sessions()
    for s in sessions:
        if s["id"] == session_id:
            return s
    return None


def create_new_session(initial_title: str | None = None) -> dict[str, Any]:
    """Create and persist a new empty chat session."""
    session = {
        "id": f"chat_{uuid.uuid4().hex[:10]}",
        "title": initial_title or "New Consultation",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "messages": [],
        "accumulated_context": {
            "symptoms": [],
            "body_locations": [],
            "negated_symptoms": [],
            "last_condition": None,
            "emergency": False,
        },
    }
    sessions = load_all_sessions()
    sessions.insert(0, session)
    save_all_sessions(sessions)
    return session


def delete_session_by_id(session_id: str) -> bool:
    """Delete a session by ID."""
    sessions = load_all_sessions()
    initial_len = len(sessions)
    sessions = [s for s in sessions if s["id"] != session_id]
    if len(sessions) < initial_len:
        save_all_sessions(sessions)
        return True
    return False


def _detect_user_challenge_or_argument(text: str) -> list[str]:
    """Identify if the user is arguing with, challenging, or refining prior conclusions."""
    challenges = []
    t = text.lower()

    if re.search(r"\b(actually|not really|i don't think|no[,.]|wrong|disagree|instead|not that)\b", t):
        challenges.append("User is directly challenging or refining previous diagnostic hypothesis.")

    if re.search(r"\b(what if|could it be|maybe it is|possible that|is it not)\b", t):
        challenges.append("User is exploring alternative differential diagnoses.")

    if re.search(r"\b(also|in addition|furthermore|plus|he also|she also)\b", t):
        challenges.append("User is introducing supplementary clinical findings to the existing case narrative.")

    if re.search(r"\b(worse|better|since|started|changed|spreading)\b", t):
        challenges.append("User is refining temporal progression or lesion severity dynamics.")

    return challenges


def _derive_model_assumptions(
    current_parse: dict[str, Any],
    history_messages: list[dict[str, Any]],
    user_text: str,
    challenge_notes: list[str],
) -> list[str]:
    """Synthesize explicit plain-language assumptions made by the model."""
    assumptions: list[str] = []
    probs = current_parse.get("condition_probabilities", {})

    # 1. Multi-turn / Argumentative assumptions
    if challenge_notes:
        for note in challenge_notes:
            assumptions.append(f"🔄 Contextual Adjustment: {note}")

    # 2. Anatomical assumptions
    locations = current_parse.get("body_locations", [])
    if locations:
        parts_desc = []
        for l in locations:
            if not l:
                continue
            side = l.get("side")
            part = l.get("part") or ""
            if side and str(side).lower() != "none":
                parts_desc.append(f"{side} {part}".strip())
            else:
                parts_desc.append(part.strip())
        parts_str = ", ".join([p for p in parts_desc if p]) or "unspecified region"
        assumptions.append(
            f"📍 Anatomical Localization: Assuming pathology is primarily situated in: {parts_str}."
        )
    else:
        assumptions.append(
            "📍 Anatomical Assumption: No specific organ or body location specified; evaluating as potential systemic or behavioral condition."
        )

    # 3. Negation scoping assumptions
    negated = current_parse.get("negated_symptoms", [])
    if negated:
        assumptions.append(
            f"🚫 Negation Assumption: Excluded {negated} as ruled-out signs; weighting zero probability toward associated etiologies."
        )

    # 4. Temporal / Chronicity assumptions
    duration = current_parse.get("duration")
    if duration:
        val = duration.get("value", 1)
        unit = duration.get("unit", "days")
        if unit == "days" and val <= 7:
            chronicity = "acute"
        elif unit == "days" and val > 7 or unit == "weeks":
            chronicity = "subacute to chronic"
        else:
            chronicity = "chronic"
        assumptions.append(
            f"⏱️ Chronicity Assumption: Categorized as an {chronicity} presentation ({val} {unit}) based on stated timeline."
        )
    else:
        assumptions.append(
            "⏱️ Temporal Assumption: No onset duration stated; assuming ongoing acute presentation pending clinician clarification."
        )

    # 5. Progression trajectory assumptions
    prog = current_parse.get("progression")
    if prog:
        assumptions.append(
            f"📈 Progression Trajectory: Assuming {prog} clinical course based on explicit owner descriptors."
        )

    # 6. Primary & Differential Hypothesis assumptions
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    if sorted_probs:
        top_k = sorted_probs[0]
        runner_up = sorted_probs[1] if len(sorted_probs) > 1 else None
        if runner_up and runner_up[1] > 0.15:
            assumptions.append(
                f"⚖️ Differential Balance: Primary assumption is '{top_k[0]}' ({top_k[1]:.0%}), but maintaining '{runner_up[0]}' ({runner_up[1]:.0%}) as a significant secondary differential."
            )
        else:
            assumptions.append(
                f"🎯 Diagnostic Assumption: High confidence convergence on '{top_k[0]}' ({top_k[1]:.0%}) based on current symptom clusters."
            )

    # 7. Emergency Guardrail assumption
    emergency = current_parse.get("emergency_triage", {})
    if emergency.get("is_critical"):
        assumptions.append(
            f"🚨 Critical Safety Assumption: Life-threatening red-flag detected ('{emergency.get('reason')}'). Deterministic safety guardrail overrides routine triage."
        )

    return assumptions


def _build_parse_entity(data: dict[str, Any]) -> SymptomParseResult:
    """Convert raw dict into domain SymptomParseResult for rule evaluation."""
    dur = data.get("duration")
    duration_ent = DurationEntity(value=dur["value"], unit=dur["unit"]) if dur else None
    triage = data.get("emergency_triage", {})
    return SymptomParseResult(
        raw_text=data.get("raw_text", ""),
        symptoms=data.get("symptoms", []),
        negated_symptoms=data.get("negated_symptoms", []),
        body_locations=[
            BodyLocation(part=loc.get("part", ""), side=loc.get("side"))
            for loc in data.get("body_locations", [])
        ],
        duration=duration_ent,
        frequency=data.get("frequency"),
        severity_cues=data.get("severity_cues", []),
        new_symptoms=data.get("new_symptoms", []),
        progression=data.get("progression"),
        behaviours=data.get("behaviours", []),
        condition_probabilities=data.get("condition_probabilities", {}),
        spans=[
            ExtractedSpan(
                entity=s["entity"],
                text=s["text"],
                start=s["start"],
                end=s["end"],
                negated=s.get("negated", False),
            )
            for s in data.get("spans", [])
        ],
        text_quality_score=data.get("text_quality_score", 0.0),
        model_confidence=data.get("model_confidence", 0.0),
        modality_reliability_score=data.get("modality_reliability_score", 0.0),
        emergency_triage=EmergencyTriageAlert(
            is_critical=triage.get("is_critical", False),
            reason=triage.get("reason"),
            recommendation=triage.get("recommendation"),
        ),
        warnings=data.get("warnings", []),
        model_version=data.get("model_version", "v1"),
    )


def _generate_conversational_reply(
    current_parse: dict[str, Any],
    assumptions: list[str],
    user_text: str,
    challenge_notes: list[str],
    clarifying_prompt: str | None = None,
) -> str:
    """Generate a helpful, empathetic, conversational clinical response."""
    emergency = current_parse.get("emergency_triage", {})
    is_critical = emergency.get("is_critical", False)
    probs = current_parse.get("condition_probabilities", {})
    top_cond = max(probs, key=probs.get) if probs else "other"
    top_prob = probs.get(top_cond, 0.0)

    cond_names = {
        "ear_inflammation": "Ear Inflammation (Otitis Externa)",
        "skin_condition": "Dermatological Condition (Allergic Dermatitis / Pruritus)",
        "eye_condition": "Ocular Condition (Conjunctivitis / Eye Discharge)",
        "other": "General / Systemic Condition",
    }

    readable_cond = cond_names.get(top_cond, top_cond.replace("_", " ").title())

    lines: list[str] = []

    # 1. Emergency immediate warning
    if is_critical:
        lines.append(
            f"⚠️ **URGENT MEDICAL ALERT:** The symptoms described involve **{emergency.get('reason', 'acute life-threatening indicators')}**."
        )
        lines.append(
            f"**Recommended Action:** {emergency.get('recommendation', 'Please take your dog to the nearest 24/7 veterinary emergency hospital immediately. Do not delay.')}\n"
        )

    # 2. Conversational acknowledgement
    if challenge_notes:
        lines.append(
            "I hear you and appreciate you clarifying that. Taking your points into consideration, I've adjusted my clinical assessment."
        )
    else:
        lines.append(
            "Thank you for sharing these clinical details about your dog."
        )

    # 3. Clinical Synthesis
    symptoms = current_parse.get("symptoms", [])
    locations = current_parse.get("body_locations", [])
    loc_str = ", ".join([f"{l.get('side') or ''} {l.get('part') or ''}".strip() for l in locations if l])

    if symptoms:
        sym_str = ", ".join([s.replace("_", " ") for s in symptoms])
        loc_clause = f" affecting the {loc_str}" if loc_str else ""
        lines.append(
            f"Based on the observed **{sym_str}**{loc_clause}, the diagnostic indicators most strongly align with **{readable_cond}** (estimated confidence: **{top_prob:.0%}**)."
        )
    else:
        lines.append(
            f"The primary impression leans toward **{readable_cond}**, though specific canonical symptom keywords were limited in this description."
        )

    # 4. Context & Actionable Advice
    if top_cond == "ear_inflammation":
        lines.append(
            "Ear canal inflammation in dogs is frequently caused by yeast or bacterial overgrowth, often secondary to moisture, allergies, or ear mites. "
            "Please refrain from probing inside the ear canal or applying over-the-counter drops before a veterinarian examines the eardrum integrity."
        )
    elif top_cond == "skin_condition":
        lines.append(
            "Pruritus, redness, or hair loss commonly stem from flea allergy dermatitis, environmental atopy, or secondary pyoderma. "
            "Using an Elizabethan collar (cone) can prevent further self-trauma and hot spot formation while scheduling a veterinary consult."
        )
    elif top_cond == "eye_condition":
        lines.append(
            "Ocular discharge, squinting, or conjunctival swelling can escalate quickly. It is important to prevent your dog from rubbing their face "
            "to avoid corneal scratches (ulcers). Seek prompt veterinary evaluation if cloudiness or severe squinting occurs."
        )
    else:
        if not is_critical:
            lines.append(
                "Monitor your dog closely for appetite changes, water intake, energy levels, and bowel movements. "
                "If symptoms persist or worsen over the next 24 to 48 hours, a formal veterinary physical exam is advised."
            )

    # 5. Targeted Clinical Intake Follow-up
    if clarifying_prompt and not is_critical:
        lines.append(f"❓ **Clinical Intake Follow-Up:**\n{clarifying_prompt}")
    elif not is_critical:
        lines.append(
            "\n*Do you notice any other signs—such as changes in appetite, foul odors, or other affected areas? Feel free to add more details or challenge this assessment!*"
        )

    return "\n\n".join(lines)


def process_user_chat_message(
    session_id: str,
    user_text: str,
    pipeline: SymptomParserPipeline,
) -> dict[str, Any]:
    """Process a user chat message, apply multi-turn context, generate assumptions, and persist."""
    session = get_session_by_id(session_id)
    if not session:
        session = create_new_session()
        session_id = session["id"]

    # 1. Store user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    user_msg = {
        "id": user_msg_id,
        "role": "user",
        "content": user_text,
        "timestamp": _now_iso(),
    }
    session["messages"].append(user_msg)

    # Update session title if first user message
    if session["title"] == "New Consultation":
        clean_title = user_text[:38].strip() + ("..." if len(user_text) > 38 else "")
        session["title"] = clean_title or "Canine Consultation"

    # 2. Check for challenge / argument cues
    challenge_notes = _detect_user_challenge_or_argument(user_text)

    # 3. Build cumulative context
    # If user is continuing/arguing, include previous clinical details
    combined_clinical_text = user_text
    prior_user_texts = [
        m["content"] for m in session["messages"][:-1] if m["role"] == "user"
    ]
    if prior_user_texts:
        combined_clinical_text = f"{' '.join(prior_user_texts[-2:])} Now: {user_text}"

    # Run inference pipeline
    parse_result = pipeline.predict(combined_clinical_text)

    # 4. Synthesize transparent clinical assumptions & evaluate clinical intake slots
    parse_entity = _build_parse_entity(parse_result)
    missing_slots = evaluate_missing_slots(parse_entity)
    user_turn_count = len([m for m in session["messages"] if m["role"] == "user"])
    clarifying_prompt = generate_clarifying_prompt(
        parse_result=parse_entity,
        missing_slots=missing_slots,
        turn_count=user_turn_count,
    )

    assumptions = _derive_model_assumptions(
        current_parse=parse_result,
        history_messages=session["messages"],
        user_text=user_text,
        challenge_notes=challenge_notes,
    )

    # 5. Generate conversational assistant reply
    assistant_reply = _generate_conversational_reply(
        current_parse=parse_result,
        assumptions=assumptions,
        user_text=user_text,
        challenge_notes=challenge_notes,
        clarifying_prompt=clarifying_prompt,
    )

    # 6. Store assistant message
    asst_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    assistant_msg = {
        "id": asst_msg_id,
        "role": "assistant",
        "content": assistant_reply,
        "timestamp": _now_iso(),
        "assumptions": assumptions,
        "clinical_data": parse_result,
        "intake_state": {
            "missing_slots": missing_slots,
            "turn_count": user_turn_count,
            "is_complete": len(missing_slots) == 0 or user_turn_count >= 4 or parse_entity.emergency_triage.is_critical,
            "clarifying_prompt": clarifying_prompt,
        },
    }
    session["messages"].append(assistant_msg)
    session["updated_at"] = _now_iso()

    # Update accumulated context
    probs = parse_result.get("condition_probabilities", {})
    top_c = max(probs, key=probs.get) if probs else "other"
    session["accumulated_context"]["last_condition"] = top_c
    session["accumulated_context"]["emergency"] = parse_result.get("emergency_triage", {}).get("is_critical", False)
    session["accumulated_context"]["symptoms"] = parse_result.get("symptoms", [])

    # Save to disk
    sessions = load_all_sessions()
    for idx, s in enumerate(sessions):
        if s["id"] == session["id"]:
            sessions[idx] = session
            break
    else:
        sessions.insert(0, session)
    save_all_sessions(sessions)

    return {
        "session_id": session_id,
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "session_title": session["title"],
    }
