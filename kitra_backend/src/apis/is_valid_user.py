from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from databases import postgres_database
from databases.error import Error

logger = logging.getLogger(__name__)

class IsUserValidResponse(BaseModel):
  message: bool

def get_router(postgres_db: postgres_database.Database) -> APIRouter:
  api = APIRouter()

  @api.get("/is_user_valid", response_model = IsUserValidResponse)
  async def is_valid_user(email: str):
    res = await postgres_db.is_email_in_database(email)
    if isinstance(res, Error):
      logger.error(res)
      raise HTTPException(status_code = 500, detail = "An internal server error happened")

    return IsUserValidResponse(message = res)

  return api
