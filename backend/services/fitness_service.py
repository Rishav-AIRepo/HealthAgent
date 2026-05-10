"""Orchestrates user profile + risk context + RAG → personalised fitness plan via LangGraph."""
from sqlalchemy.orm import Session
from backend.db import models
from backend.agents.intake_agent import run_intake_agent
from backend.agents.graph import build_health_graph
from backend.services.embedding_service import load_retriever

_FALLBACK_PLAN = {
    "workout": ["Walking 30 min/day", "Light stretching"],
    "diet": ["Balanced meals", "Reduce processed sugar"],
    "restrictions": ["Consult physician before starting any exercise"],
    "lifestyle": ["7-8 hours sleep", "Stress management"],
}


async def get_fitness_plan(user_id: str, db: Session) -> dict:
    user: models.User | None = db.query(models.User).filter_by(user_id=user_id).first()
    records: list[models.HealthRecord] = (
        db.query(models.HealthRecord).filter_by(user_id=user_id).all()
    )

    age = user.age if user else 30
    gender = user.gender if user else "other"
    bmi = 22.0
    if user:
        intake = run_intake_agent(user.age, user.gender, user.height_cm, user.weight_kg)
        bmi = intake.bmi

    # Load RAG context — query with flagged param names for relevance
    rag_context = ""
    retriever = load_retriever(user_id)
    if retriever and records:
        flagged_names = [r.parameter for r in records if r.status != "Normal"]
        query = ", ".join(flagged_names) if flagged_names else "health fitness diet recommendations"
        try:
            docs = retriever.invoke(query)
            rag_context = "\n\n".join(d.page_content for d in docs)
        except Exception:
            pass

    # Run full LangGraph pipeline: disease_detection → risk_analysis → fitness_planning
    graph = build_health_graph()
    initial_state = {
        "user_id": user_id,
        "age": age,
        "gender": gender,
        "bmi": bmi,
        "records": records,
        "conditions": [],
        "risk_score": 0,
        "risk_level": "Low",
        "risk_summary": "",
        "flagged_params": [],
        "rag_context": rag_context,
        "fitness_plan": None,
    }

    try:
        final_state = await graph.ainvoke(initial_state)
        return final_state.get("fitness_plan") or _FALLBACK_PLAN
    except Exception:
        return _FALLBACK_PLAN
