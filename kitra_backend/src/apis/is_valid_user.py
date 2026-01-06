from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from databases import postgres_database

logger = logging.getLogger(__name__)

class IsUserValidResponse(BaseModel):
  message: bool

def get_router(postgres_db: postgres_database.Database) -> APIRouter:
  api = APIRouter()

  @api.get("/is_user_valid", response_model = IsUserValidResponse)
  async def is_valid_user(email: str):
    res = await postgres_db.is_email_in_database(email)
    if res[0] != 0:
      logger.error(res[1])
      raise HTTPException(status_code = 500, detail = "An internal server error happened")

    ans: bool = False
    if res[1][0]:
      ans: bool = True

    return IsUserValidResponse(message = ans)

  return api
