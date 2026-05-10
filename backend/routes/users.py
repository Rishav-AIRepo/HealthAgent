from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.models.schemas import UserProfile, UserProfileResponse
from backend.utils.auth_dep import get_current_user

router = APIRouter()


@router.post("/", response_model=UserProfileResponse)
def create_or_update_user(
    profile: UserProfile,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["sub"] != profile.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(models.User).filter_by(user_id=profile.user_id).first()
    if user:
        user.age = profile.age
        user.gender = profile.gender
        user.height_cm = profile.height_cm
        user.weight_kg = profile.weight_kg
    else:
        user = models.User(
            user_id=profile.user_id,
            age=profile.age,
            gender=profile.gender,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return UserProfileResponse(
        user_id=user.user_id,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        email=user.email,
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(models.User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfileResponse(
        user_id=user.user_id,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        email=user.email,
    )
