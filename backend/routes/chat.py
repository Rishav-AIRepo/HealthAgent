from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.agents.disease_agent import run_disease_agent
from backend.agents.risk_agent import compute_risk_score
from backend.agents.intake_agent import run_intake_agent
from backend.services.embedding_service import load_retriever
from backend.utils.llm_factory import get_llm
from backend.utils.prompt_templates import ENRICHED_CHAT_PROMPT, SYSTEM_GUARDRAIL
from backend.utils.auth_dep import get_current_user
from backend.models.schemas import ChatRequest, ChatResponse
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter()


def _build_health_summary(user, records: list, bmi: float) -> str:
    """Compose a compact structured summary of the patient's health state."""
    lines = []
    if user:
        lines.append(f"Age: {user.age} | Gender: {user.gender} | BMI: {bmi:.1f}")

    if records:
        _, risk_level = compute_risk_score(records)
        conditions = run_disease_agent(records)
        lines.append(f"Risk Level: {risk_level}")
        if conditions:
            lines.append(f"Detected Conditions: {', '.join(conditions)}")

        flagged = [r for r in records if r.status != "Normal"]
        if flagged:
            lines.append("Flagged Lab Parameters:")
            for r in flagged:
                lines.append(
                    f"  - {r.parameter}: {r.value} {r.unit}  "
                    f"[ref: {r.reference_range}]  Status: {r.status}"
                )
        normal_count = len(records) - len(flagged)
        lines.append(f"Normal parameters: {normal_count}/{len(records)}")
    else:
        lines.append("No health records on file.")

    return "\n".join(lines)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["sub"] != request.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    # ── 1. Load user & health records ────────────────────────
    user = db.query(models.User).filter_by(user_id=request.user_id).first()
    records: list[models.HealthRecord] = (
        db.query(models.HealthRecord).filter_by(user_id=request.user_id).all()
    )

    if not records:
        answer = (
            "No health records found for your account. "
            "Please upload a lab report PDF first so I can answer questions about your health."
        )
        _persist(db, request, answer)
        return ChatResponse(answer=answer)

    # ── 2. Build structured health summary ───────────────────
    bmi = 22.0
    if user:
        intake = run_intake_agent(user.age, user.gender, user.height_cm, user.weight_kg)
        bmi = intake.bmi
    health_summary = _build_health_summary(user, records, bmi)

    # ── 3. RAG retrieval ─────────────────────────────────────
    rag_context = "No additional document context available."
    retriever = load_retriever(request.user_id)
    if retriever:
        try:
            docs = retriever.invoke(request.query)
            rag_context = "\n\n".join(d.page_content for d in docs)
        except Exception:
            pass

    # ── 4. LLM call with enriched context ────────────────────
    prompt = ENRICHED_CHAT_PROMPT.format(
        health_summary=health_summary,
        rag_context=rag_context,
        question=request.query,
    )
    llm = get_llm()
    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM_GUARDRAIL),
        HumanMessage(content=prompt),
    ])
    answer = response.content.strip()

    # ── 5. Persist conversation ───────────────────────────────
    _persist(db, request, answer)

    return ChatResponse(
        answer=answer,
        disclaimer="This is not medical advice. Always consult a qualified physician.",
    )


def _persist(db: Session, request: ChatRequest, answer: str) -> None:
    for role, content in [("user", request.query), ("assistant", answer)]:
        db.add(models.ChatMessage(
            session_id=request.session_id,
            user_id=request.user_id,
            role=role,
            content=content,
        ))
    db.commit()
