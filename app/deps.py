from fastapi import Header, HTTPException, status
from .settings import settings
from .auth_handler import encodeJWT, decodeJWT
ADMIN_SET = {r.strip().lower() for r in settings.ADMIN_ROLES.split(',') if r.strip()}
ADMIN_SECRET = settings.SECRET_KEY

def require_admin(authorization: str | None = Header(default=None, alias="Authorization")):
  if not decodeJWT(authorization):
    raise HTTPException(status_code=401, detail="Token JWT is expired")
  return authorization.lower()
