from fastapi import APIRouter

import logging

from databases import postgres_database, redis_database

from . import login
from . import logout
from . import renew_refresh_token
from . import renew_session_token
from . import is_valid_user

def get_router(postgres_db: postgres_database.Database, redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  api.include_router(login.get_router(postgres_db, redis_db))
  api.include_router(logout.get_router(redis_db))
  api.include_router(renew_refresh_token.get_router(redis_db))
  api.include_router(renew_session_token.get_router(redis_db))
  api.include_router(is_valid_user.get_router(postgres_db))

  return api
