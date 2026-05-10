from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.services.fitness_service import get_fitness_plan
from backend.models.schemas import FitnessPlanRequest, FitnessPlanResponse
from backend.utils.plan_guard import require_plan

router = APIRouter()


@router.post("/plan", response_model=FitnessPlanResponse)
async def generate_plan(
    request: FitnessPlanRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_plan("standard")),
):
    if current_user["sub"] != request.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    plan = await get_fitness_plan(request.user_id, db)
    return FitnessPlanResponse(**plan)
