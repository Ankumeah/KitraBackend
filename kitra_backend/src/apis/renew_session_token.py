from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import logging
import time

from databases import redis_database

logger = logging.getLogger(__name__)

class RenewSessionTokenRequest(BaseModel):
  email: str
  refresh_token: str

class RenewSessionTokenResponse(BaseModel):
  session_token: str
  session_token_expire: int

def get_router(redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  @api.post("/renew_session_token", response_model = RenewSessionTokenResponse)
  async def renew_session_token(data: RenewSessionTokenRequest):
    email: str = data.email
    if not email:
      raise HTTPException(status_code = 400, detail = "Provide a email")

    refresh_token: str = data.refresh_token
    if not refresh_token:
      raise HTTPException(status_code = 400, detail = "Provide a refresh_token")

    res = await redis_db.get_session_token_id(email, refresh_token)
    expire: int = int(time.time()) + redis_db.SESSION_TOKEN_EXPIRY
    if res[0] != 0:
      if res[0] == -1:
        logger.error(res[1])
        raise HTTPException(status_code = 500, detail = "An internal server error happened")
      elif res[1] == "False":
        raise HTTPException(status_code = 401, detail = "refresh_token is invalid")
      else:
        raise HTTPException(status_code = 400, detail = res[1])

    res = await redis_db.add_session_token_entry(email, refresh_token)
    if res[0] != 0:
      if res[0] == -1:
        logger.error(res[1])
        raise HTTPException(status_code = 500, detail = "An internal server error happened")
      else:
        raise HTTPException(status_code = 401, detail = res[1])

    return RenewSessionTokenResponse(
      session_token = res[1],
      session_token_expire = expire
    )

  return api
