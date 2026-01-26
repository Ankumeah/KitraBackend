from fastapi import FastAPI
import yaml

import os
import sys
import logging
import logging.config
from contextlib import asynccontextmanager

from databases import postgres_database, redis_database
import wss

def log_setup():
  LOGFILE_PATH: str = os.path.join("logs", "wss", "logfile")
  LOGFILE_SIZE: int = 1024 * 1024 * 1024

  try:
    os.makedirs(os.path.join("logs", "wss"), exist_ok = True)

    with open("logging_conf.yaml") as f:
      conf = yaml.safe_load(f)
      conf["handlers"]["logfile"]["filename"] = LOGFILE_PATH
      conf["handlers"]["logfile"]["maxBytes"] = LOGFILE_SIZE

      logging.config.dictConfig(conf)

  except Exception as e:
    print(f"Unable to load logger config: {e}")
    sys.exit(1)

  return logging.getLogger("KitraBackend (WS)")

logger = log_setup()

@asynccontextmanager
async def lifespan(ws: FastAPI):
  postgres_db = postgres_database.Database()
  postgres_init_res = await postgres_db.init_db()

  redis_db = redis_database.RedisDatabase()

  if postgres_init_res[0] != 0:
    logger.error(postgres_init_res[1])
    sys.exit(1)

  ws.include_router(wss.get_router(postgres_db, redis_db), prefix = "/ws")

  logger.info("new WS worker started")

  yield

  logger.info("Clearing all websocket connections")
  await wss.exchange_messages.pool.remove_all_clients()

  logger.info("Closeing database pool")
  await postgres_db.POSTGRES_POOL.close()

  logger.info("WS worker stopped")

ws = FastAPI(
  lifespan = lifespan,
  docs_url = "/ws/docs",
  redoc_url = "/ws/redoc",
  openapi_url = "/ws/openapi.json"
)
