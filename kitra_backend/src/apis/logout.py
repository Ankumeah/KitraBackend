from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import logging

from databases import redis_database

logger = logging.getLogger(__name__)

class LogoutRequest(BaseModel):
  email: str
  refresh_token: str

class LogoutResponse(BaseModel):
  message: str

def get_router(redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  @api.post("/logout", response_model = LogoutResponse)
  async def logout(data: LogoutRequest):
    email: str = data.email
    if not email:
      raise HTTPException(status_code = 400, detail = "Provide a email")

    refresh_token: str = data.refresh_token
    if not refresh_token:
      raise HTTPException(status_code = 400, detail = "Provide a refresh_token")

    res = await redis_db.remove_user_session(email, refresh_token)
    if res[0] != 0:
      if res[0] == -1:
        logger.error(res[1])
        raise HTTPException(status_code = 500, detail = "An internal server error happened")
      else:
        raise HTTPException(status_code = 400, detail = res[1])

    return LogoutResponse(message = "Success")

  return api
