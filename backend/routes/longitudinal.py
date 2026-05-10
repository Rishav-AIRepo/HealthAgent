from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.utils.plan_guard import require_plan
from backend.services.longitudinal_service import analyse

router = APIRouter()


@router.get("/{user_id}")
async def longitudinal_analysis(
    user_id: str,
    current_user: dict = Depends(require_plan("standard")),
    db: Session = Depends(get_db),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    snapshots = (
        db.query(models.LongitudinalSnapshot)
        .filter(models.LongitudinalSnapshot.user_id == user_id)
        .order_by(models.LongitudinalSnapshot.snapshot_date.asc())
        .all()
    )

    if len(snapshots) < 2:
        return {"message": "Upload at least 2 PDFs to see longitudinal analysis"}

    return await analyse(user_id, snapshots, db)
