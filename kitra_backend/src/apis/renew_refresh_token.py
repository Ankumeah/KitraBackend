from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import logging
import time

from databases import redis_database

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
    if res[0] != 0:
      if res[0] == -1:
        logger.error(res[1])
        raise HTTPException(status_code = 500, detail = "An internal server error happened")
      elif res[1] == "False":
        raise HTTPException(status_code = 401, detail = "refresh_token is invalid")
      else:
        raise HTTPException(status_code = 400, detail = res[1])

    res = await redis_db.add_refresh_token_entry(email)
    expire: int = int(time.time()) + redis_db.REFRESH_TOKEN_EXPIRY

    if res[0] != 0:
      if res[0] == -1:
        logger.error(res[1])
        raise HTTPException(status_code = 500, detail = "An internal server error happened")
      else:
        raise HTTPException(status_code = 401, detail = res[1])

    return RenewRefreshTokenResponse(refresh_token = res[1], refresh_token_expire = expire)

  return api
