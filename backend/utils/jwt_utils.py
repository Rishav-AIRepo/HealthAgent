from jose import jwt
from datetime import datetime, timedelta
from config.settings import get_settings

settings = get_settings()


def create_access_token(data: dict, expires_minutes: int = 1440) -> str:
    payload = {**data, "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, settings.app_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
