from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.utils.auth_dep import get_current_user

router = APIRouter()


@router.get("/{user_id}")
async def get_trends(
    user_id: str,
    parameters: str = Query("glucose,cholesterol,hemoglobin,creatinine"),
    days: int = Query(180),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    param_list = [p.strip().lower() for p in parameters.split(",")]
    since = datetime.utcnow() - timedelta(days=days)

    records = (
        db.query(models.HealthRecord)
        .filter(
            models.HealthRecord.user_id == user_id,
            models.HealthRecord.recorded_at >= since,
        )
        .order_by(models.HealthRecord.recorded_at.asc())
        .all()
    )

    # Group by matching parameter (case-insensitive substring), track unit per param
    grouped: dict[str, list] = defaultdict(list)
    units: dict[str, str] = {}
    for r in records:
        for param in param_list:
            if param in r.parameter.lower():
                grouped[param].append({
                    "date": r.recorded_at.date().isoformat() if r.recorded_at else "",
                    "value": float(r.value),
                    "file_id": r.file_id or "",
                })
                if param not in units:
                    units[param] = r.unit or ""

    # Risk score series from longitudinal snapshots
    snapshots = (
        db.query(models.LongitudinalSnapshot)
        .filter(
            models.LongitudinalSnapshot.user_id == user_id,
            models.LongitudinalSnapshot.snapshot_date >= since.date(),
        )
        .order_by(models.LongitudinalSnapshot.snapshot_date.asc())
        .all()
    )

    risk_over_time = [
        {
            "date": s.snapshot_date.isoformat(),
            "risk_score": s.risk_score or 0,
            "risk_level": s.risk_level or "Low",
        }
        for s in snapshots
    ]

    return {
        "user_id": user_id,
        "series": [
            {
                "parameter": p,
                "unit": units.get(p, ""),
                "data_points": grouped[p],
            }
            for p in param_list
            if p in grouped
        ],
        "risk_over_time": risk_over_time,
        "days": days,
    }
