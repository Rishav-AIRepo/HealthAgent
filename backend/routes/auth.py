"""Auth routes — stateless Google OAuth using JWT-signed state (no session cookie)."""
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.db import models
from backend.db.database import get_db
from backend.utils.auth_dep import get_current_user
from backend.utils.jwt_utils import create_access_token
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

_ALGO = "HS256"
_STATE_TTL = 600  # 10 minutes


def _make_state() -> str:
    payload = {
        "jti": secrets.token_urlsafe(16),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=_STATE_TTL),
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=_ALGO)


def _verify_state(state: str) -> bool:
    try:
        jwt.decode(state, settings.app_secret_key, algorithms=[_ALGO])
        return True
    except JWTError:
        return False


@router.get("/login")
async def login(request: Request):
    state = _make_state()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
    }
    google_url = "https://accounts.google.com/o/oauth2/v2/auth"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(url=f"{google_url}?{query}")


@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error={error}"
        )

    state = request.query_params.get("state", "")
    code = request.query_params.get("code", "")

    if not _verify_state(state):
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?error=invalid_state"
        )

    # Exchange code for tokens — no session required
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()

    # Fetch user info
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo_resp.raise_for_status()
        user_info = userinfo_resp.json()

    email = user_info["email"]
    sub = user_info["sub"]

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(user_id=sub, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token({"sub": user.user_id, "email": user.email})
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/success?token={jwt_token}"
    )


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter_by(user_id=current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"sub": user.user_id, "email": user.email}
