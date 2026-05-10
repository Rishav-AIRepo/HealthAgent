from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import models
from backend.utils.jwt_utils import create_access_token
from backend.utils.auth_dep import get_current_user
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login")
async def login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    user = db.query(models.User).filter(models.User.email == user_info["email"]).first()
    if not user:
        user = models.User(user_id=user_info["sub"], email=user_info["email"])
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token({"sub": user.user_id, "email": user.email})
    return RedirectResponse(url=f"{settings.frontend_url}/auth/success?token={jwt_token}")


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter_by(user_id=current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"sub": user.user_id, "email": user.email}
