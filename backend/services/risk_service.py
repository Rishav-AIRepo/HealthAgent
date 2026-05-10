"""Orchestrates the full health-analysis pipeline for a given user."""
from sqlalchemy.orm import Session
from backend.db import models
from backend.agents.intake_agent import run_intake_agent
from backend.agents.disease_agent import run_disease_agent
from backend.agents.risk_agent import compute_risk_score, run_risk_agent


async def get_full_risk_analysis(user_id: str, db: Session) -> dict:
    user: models.User | None = db.query(models.User).filter_by(user_id=user_id).first()
    records: list[models.HealthRecord] = (
        db.query(models.HealthRecord).filter_by(user_id=user_id).all()
    )

    if not records:
        return {
            "user_id": user_id,
            "risk_score": 0,
            "risk_level": "Low",
            "flagged_parameters": [],
            "conditions": [],
            "recommendation": "No health records found. Please upload a lab report PDF.",
        }

    # Compute vitals if user profile exists
    bmi = 22.0  # default
    age = user.age if user else 30
    gender = user.gender if user else "other"
    if user:
        intake = run_intake_agent(user.age, user.gender, user.height_cm, user.weight_kg)
        bmi = intake.bmi

    conditions = run_disease_agent(records)
    risk_score, risk_level = compute_risk_score(records)
    recommendation = await run_risk_agent(user_id, age, gender, bmi, records, conditions)

    flagged = [
        {
            "test_name": r.parameter,
            "value": r.value,
            "unit": r.unit,
            "reference_range": r.reference_range,
            "status": r.status,
        }
        for r in records
        if r.status != "Normal"
    ]

    return {
        "user_id": user_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flagged_parameters": flagged,
        "conditions": conditions,
        "recommendation": recommendation,
    }
