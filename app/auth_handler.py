from .settings import settings
import time
from typing import Dict
import jwt
SECRET = settings.SECRET_KEY

def encodeJWT() -> Dict[str, str]:
    payload = {
        "id": settings.ADMIN,
        "expires": time.time() + 3600
    }
    token = jwt.encode(payload, SECRET, algorithm='HS256')

    return {"token" : token}

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, SECRET, algorithms=['HS256'])
        if decoded_token["expires"] >= time.time() and decoded_token["id"] == settings.ADMIN:
            return decoded_token
        else: 
            return None
    except: 
        return {}