from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import time
import logging

from databases import postgres_database, redis_database, validations
from databases.error import Error

logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
  JWT_token: str

class LoginResponse(BaseModel):
  session_token: str
  session_token_expire: int
  refresh_token: str
  refresh_token_expire: int

def get_router(postgres_db: postgres_database.Database, redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  @api.post("/login", response_model = LoginResponse)
  async def login(data: LoginRequest):
    info = validations.validate_JWT_token(data.JWT_token)
    if info[0] == 500:
      raise HTTPException(status_code = info[0], detail = "An internal error happened")
    if info[0] == 401:
      raise HTTPException(status_code = info[0], detail = "Invalid JWT")

    info = info[1]

    email: str = info.get("email", "")

    res = await postgres_db.is_email_in_database(email)
    if isinstance(res, Error):
      logger.error(res)
      raise HTTPException(status_code = 500, detail = "An internal error happened")

    res = await postgres_db.add_user(email)

    if isinstance(res, Error):
      logger.error(res)
      raise HTTPException(status_code = 500, detail = "An internal error happened")

    refresh_res = await redis_db.add_refresh_token_entry(email)
    if refresh_res[0] != 0:
      raise HTTPException(status_code = 401, detail = refresh_res[1])
    refresh_token_expire: float = int(time.time()) + redis_db.REFRESH_TOKEN_EXPIRY

    session_res = await redis_db.add_session_token_entry(email, refresh_res[1])
    if session_res[0] != 0:
      raise HTTPException(status_code = 401, detail = session_res[1])
    session_token_expire: float = int(time.time()) + redis_db.SESSION_TOKEN_EXPIRY

    return LoginResponse(
      session_token = session_res[1],
      session_token_expire = session_token_expire,
      refresh_token = refresh_res[1],
      refresh_token_expire = refresh_token_expire
    )

  return api
