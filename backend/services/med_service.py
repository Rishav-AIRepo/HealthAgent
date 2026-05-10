"""Medication orchestration service."""
from backend.db import models
from backend.agents.med_interaction_agent import run_med_interaction_agent
from backend.agents.disease_agent import run_disease_agent
from config.settings import get_settings

settings = get_settings()


async def get_interactions(user_id: str, db) -> dict:
    meds = (
        db.query(models.Medication)
        .filter_by(user_id=user_id, is_active=True)
        .all()
    )
    medication_names = [f"{m.name} {m.dosage}".strip() for m in meds]

    records = db.query(models.HealthRecord).filter_by(user_id=user_id).all()
    conditions = run_disease_agent(records) if records else []
    flagged = [
        {
            "test_name": r.parameter,
            "value": r.value,
            "unit": r.unit,
            "status": r.status,
        }
        for r in records
        if r.status != "Normal"
    ]

    result = await run_med_interaction_agent(
        medications=medication_names,
        conditions=conditions,
        flagged_params=flagged,
        drug_knowledge_path=settings.drug_knowledge_path,
    )
    result["user_id"] = user_id
    result["disclaimer"] = (
        "This AI-generated analysis is not a substitute for professional pharmacist or "
        "physician advice. Never change or stop medications without consulting your doctor."
    )
    return result
