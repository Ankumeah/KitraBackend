from fastapi import APIRouter

from databases import postgres_database, redis_database

from . import exchange_messages

def get_router(postgres_db: postgres_database.Database, redis_db: redis_database.RedisDatabase) -> APIRouter:
  ws = APIRouter()

  ws.include_router(exchange_messages.get_router(postgres_db = postgres_db, redis_db = redis_db))

  return ws
