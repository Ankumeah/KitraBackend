from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import logging
import time

from databases import redis_database
from databases.error import Error

logger = logging.getLogger(__name__)

class RenewRefreshTokenRequest(BaseModel):
  email: str
  refresh_token: str

class RenewRefreshTokenResponse(BaseModel):
  refresh_token: str
  refresh_token_expire: int

def get_router(redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  @api.post("/renew_refresh_token", response_model = RenewRefreshTokenResponse)
  async def renew_refresh_token(data: RenewRefreshTokenRequest):
    email: str = data.email
    if not email:
      raise HTTPException(status_code = 400, detail = "Provide a email")

    refresh_token: str = data.refresh_token
    if not refresh_token:
      raise HTTPException(status_code = 400, detail = "Provide a refresh_token")

    res = await redis_db.is_refresh_token_valid(email, refresh_token)
    if isinstance(res, Error):
      logger.error(res.error)
      raise HTTPException(status_code = 500, detail = "An internal server error happened")
    elif not res:
      raise HTTPException(status_code = 401, detail = "refresh_token is invalid")

    res = await redis_db.add_refresh_token_entry(email)
    expire: int = int(time.time()) + redis_db.REFRESH_TOKEN_EXPIRY

    if isinstance(res, Error):
      logger.error(res.error)
      raise HTTPException(status_code = 500, detail = "An internal server error happened")
    elif res == "-1":
      raise HTTPException(status_code = 401, detail = "Invalid email or too many refresh_tokens")

    return RenewRefreshTokenResponse(refresh_token = res, refresh_token_expire = expire)

  return api
