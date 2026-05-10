from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.utils.auth_dep import get_current_user

PDF_LIMITS = {"free": 2, "standard": 15, "premium": 999999}
PLAN_ORDER = ["free", "standard", "premium"]


def require_plan(min_plan: str):
    def guard(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        sub = (
            db.query(models.Subscription)
            .filter(models.Subscription.user_id == current_user["sub"])
            .first()
        )
        user_plan = sub.plan if sub else "free"
        if PLAN_ORDER.index(user_plan) < PLAN_ORDER.index(min_plan):
            raise HTTPException(
                status_code=402,
                detail=f"Upgrade to {min_plan} to use this feature",
            )
        return current_user

    return guard


def check_upload_quota(user_id: str, db: Session) -> None:
    sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == user_id)
        .first()
    )
    plan = sub.plan if sub else "free"
    limit = PDF_LIMITS[plan]
    count = sub.upload_count if sub else 0
    if count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Upload limit reached ({limit}/month). Upgrade your plan.",
        )


def increment_upload_count(user_id: str, db: Session) -> None:
    sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == user_id)
        .first()
    )
    if sub:
        sub.upload_count = (sub.upload_count or 0) + 1
        db.commit()
