from fastapi import (
  APIRouter,
  WebSocket,
  WebSocketDisconnect,
  WebSocketException,
  status
)
from pydantic import BaseModel, ValidationError

import logging

from databases import (
  redis_database,
  postgres_database,
  websocket_manager,
  validations,
)
from databases.error import Error

logger = logging.getLogger(__name__)

class FirstRequest(BaseModel):
  session_token: str
  email: str

class Request(BaseModel):
  session_token: str
  receiver_email: str
  content: str

class Response(BaseModel):
  sender_email: str
  content: str
  unix_time: int

pool = websocket_manager.WebSocketManager()

def get_router(postgres_db: postgres_database.Database, redis_db: redis_database.RedisDatabase) -> APIRouter:
  api = APIRouter()

  async def validate_first_message(socket: WebSocket, data: str) -> FirstRequest:
    first_model: FirstRequest | None = None

    try:
      first_model = FirstRequest.model_validate_json(data)
    except ValidationError:
      raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

    if not validations.is_valid_email(first_model.email):
      raise WebSocketException(status.WS_1008_POLICY_VIOLATION)

    if pool.is_duplicate_session(first_model.email, first_model.session_token):
      raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

    res: bool | Error = await redis_db.is_session_token_valid(first_model.email, first_model.session_token)
    if isinstance(res, Error):
      logger.error(res.error)
      raise WebSocketException(status.WS_1011_INTERNAL_ERROR)
    elif not res:
      raise WebSocketException(status.WS_1008_POLICY_VIOLATION)
    else:
      pool.add_connection(socket, first_model.email, first_model.session_token)

    return first_model

  async def validate_message(data: str, first_model: FirstRequest) -> Request:
    try:
      model: Request = Request.model_validate_json(data)
    except ValidationError:
      raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

    if len(model.content) > 2000:
      raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

    res: bool | Error = await redis_db.is_session_token_valid(first_model.email, model.session_token)
    if isinstance(res, Error):
      logger.error(res.error)
      raise WebSocketException(status.WS_1011_INTERNAL_ERROR)
    if not res:
      raise WebSocketException(status.WS_1008_POLICY_VIOLATION)
    else:
      return model

  @api.websocket("/exchange_messages")
  async def exchange_messages(socket: WebSocket):
    await socket.accept()

    first_model: FirstRequest | None = None

    try:
      data: str = await socket.receive_text()
      first_model = await validate_first_message(socket, data)

      while True:
        data: str = await socket.receive_text()

        model: Request = await validate_message(data, first_model)

        res_msg: int | Error = await postgres_db.send_message(first_model.email, model.receiver_email, model.content)
        if isinstance(res_msg, Error):
          raise WebSocketException(status.WS_1007_INVALID_FRAME_PAYLOAD_DATA)

        for client in pool.get_clients(model.receiver_email):
          await client.send_json(Response(
            sender_email = first_model.email,
            content = model.content,
            unix_time = res_msg
          ).model_dump())

    except WebSocketDisconnect:
      logger.debug(f"Client Disconnected {socket.client}")

    finally:
      if first_model and pool.is_duplicate_session(first_model.email, first_model.session_token):
        pool.remove_connection(first_model.email, socket)

  return api
