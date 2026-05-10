from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.risk_service import get_full_risk_analysis
from backend.models.schemas import InsightResponse
from backend.utils.auth_dep import get_current_user

router = APIRouter()


@router.get("/{user_id}", response_model=InsightResponse)
async def get_insights(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    result = await get_full_risk_analysis(user_id, db)
    return InsightResponse(**result)
