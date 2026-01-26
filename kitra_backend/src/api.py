from fastapi import FastAPI
import yaml

import os
import sys
import logging
import logging.config
from contextlib import asynccontextmanager

from databases import postgres_database, redis_database
import apis

def log_setup():
  LOGFILE_PATH: str = os.path.join("logs", "apis", "logfile")
  LOGFILE_SIZE: int = 1024 * 1024 * 1024

  try:
    os.makedirs(os.path.join("logs", "apis"), exist_ok = True)

    with open("logging_conf.yaml") as f:
      conf = yaml.safe_load(f)
      conf["handlers"]["logfile"]["filename"] = LOGFILE_PATH
      conf["handlers"]["logfile"]["maxBytes"] = LOGFILE_SIZE

      logging.config.dictConfig(conf)

  except Exception as e:
    print(f"Unable to load logger config: {e}")
    sys.exit(1)

  return logging.getLogger("KitraBackend (API)")

logger = log_setup()

@asynccontextmanager
async def lifespan(api: FastAPI):
  postgres_db = postgres_database.Database()
  postgres_init_res = await postgres_db.init_db()

  redis_db = redis_database.RedisDatabase()

  if postgres_init_res[0] != 0:
    logger.error(postgres_init_res[1])
    sys.exit(1)

  api.include_router(apis.get_router(postgres_db, redis_db), prefix = "/api")

  logger.info("new API worker started")
  yield

  logger.info("Closeing database pool")
  await postgres_db.POSTGRES_POOL.close()

  logger.info("API worker stopped")

api = FastAPI(
  lifespan = lifespan,
  docs_url = "/api/docs",
  redoc_url = "/api/redoc",
  openapi_url = "/api/openapi.json"
)
