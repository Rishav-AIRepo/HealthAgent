from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.models.schemas import (
    MedicationCreate, MedicationUpdate, MedicationLogCreate,
)
from backend.utils.auth_dep import get_current_user
from backend.utils.plan_guard import require_plan

router = APIRouter()


def _med_to_dict(m: models.Medication) -> dict:
    return {
        "id": m.id,
        "user_id": m.user_id,
        "name": m.name,
        "dosage": m.dosage,
        "frequency": m.frequency,
        "start_date": m.start_date.isoformat() if m.start_date else None,
        "end_date": m.end_date.isoformat() if m.end_date else None,
        "is_active": m.is_active,
        "notes": m.notes,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.post("/")
async def add_medication(
    payload: MedicationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = (
        date.fromisoformat(payload.start_date)
        if payload.start_date
        else date.today()
    )
    med = models.Medication(
        user_id=current_user["sub"],
        name=payload.name,
        dosage=payload.dosage,
        frequency=payload.frequency,
        start_date=start,
        end_date=date.fromisoformat(payload.end_date) if payload.end_date else None,
        notes=payload.notes,
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return _med_to_dict(med)


@router.get("/{user_id}")
async def list_medications(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    meds = db.query(models.Medication).filter_by(user_id=user_id, is_active=True).all()
    return [_med_to_dict(m) for m in meds]


@router.put("/{med_id}")
async def update_medication(
    med_id: int,
    payload: MedicationUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    med = db.query(models.Medication).filter_by(id=med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    if med.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, val in payload.model_dump(exclude_none=True).items():
        if field == "end_date" and val:
            setattr(med, field, date.fromisoformat(val))
        else:
            setattr(med, field, val)
    db.commit()
    db.refresh(med)
    return _med_to_dict(med)


@router.delete("/{med_id}")
async def deactivate_medication(
    med_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    med = db.query(models.Medication).filter_by(id=med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    if med.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    med.is_active = False
    db.commit()
    return {"message": "Medication deactivated"}


@router.post("/{med_id}/log")
async def log_medication(
    med_id: int,
    payload: MedicationLogCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    med = db.query(models.Medication).filter_by(id=med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")
    if med.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    log_entry = models.MedicationLog(
        medication_id=med_id,
        user_id=current_user["sub"],
        status=payload.status,
        notes=payload.notes,
    )
    db.add(log_entry)
    db.commit()
    return {"message": "Log recorded", "status": payload.status}


@router.get("/{user_id}/adherence")
async def get_adherence(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    since = datetime.utcnow() - timedelta(days=30)
    meds = (
        db.query(models.Medication)
        .filter_by(user_id=user_id, is_active=True)
        .all()
    )

    adherence = []
    for med in meds:
        logs = (
            db.query(models.MedicationLog)
            .filter(
                models.MedicationLog.medication_id == med.id,
                models.MedicationLog.taken_at >= since,
            )
            .all()
        )
        total = len(logs)
        taken = sum(1 for lg in logs if lg.status == "taken")
        adherence.append({
            "medication_id": med.id,
            "medication_name": med.name,
            "total_logs": total,
            "taken_count": taken,
            "adherence_pct": round(taken / total * 100, 1) if total > 0 else 0.0,
        })

    return {"user_id": user_id, "adherence": adherence}


@router.get("/{user_id}/interactions")
async def check_interactions(
    user_id: str,
    current_user: dict = Depends(require_plan("standard")),
    db: Session = Depends(get_db),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    from backend.services.med_service import get_interactions
    return await get_interactions(user_id, db)
