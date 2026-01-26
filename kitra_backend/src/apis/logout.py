from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import logging

from databases import redis_database
from databases.error import Error

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
    if isinstance(res, Error):
      logger.error(res.error)
      raise HTTPException(status_code = 500, detail = "An internal server error happened")
    elif not res:
      raise HTTPException(status_code = 400, detail = "Invalid email or refresh_token")

    return LogoutResponse(message = "Success")

  return api
