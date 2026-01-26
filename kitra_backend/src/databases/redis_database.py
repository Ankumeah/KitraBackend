import os
import redis.asyncio as redis
import secrets
import hashlib
import logging

from . import validations

class RedisDatabase:
  logger = logging.getLogger(__name__)

  MAX_ALLOWED_REFRESH_TOKENS: int = 10
  MAX_ALLOWED_SESSION_TOKENS: int = 20

  REFRESH_TOKEN_LENGTH: int = 256
  SESSION_TOKEN_LENGTH: int = 64

  REFRESH_TOKEN_EXPIRY: int = 60 * 60 * 24 * 30
  SESSION_TOKEN_EXPIRY: int = 60 * 60

  def __init__(self) -> None:
    self.REDIS_HOST: str = os.environ.get("REDIS_HOST", "")
    self.REDIS_PORT: str = os.environ.get("REDIS_PORT", "")
    self.REDIS_SESSION_USER_USERNAME: str = os.environ.get("REDIS_SESSION_USER_USERNAME", "")
    self.REDIS_REFRESH_USER_USERNAME: str = os.environ.get("REDIS_REFRESH_USER_USERNAME", "")
    self.REDIS_SESSION_USER_PASSWORD: str = os.environ.get("REDIS_SESSION_USER_PASSWORD", "")
    self.REDIS_REFRESH_USER_PASSWORD: str = os.environ.get("REDIS_REFRESH_USER_PASSWORD", "")

    if not self.REDIS_HOST: raise RuntimeError("REDIS_HOST not set")
    if not self.REDIS_PORT: raise RuntimeError("REDIS_PORT not set")
    if not self.REDIS_SESSION_USER_USERNAME: raise RuntimeError("REDIS_SESSION_USER_USERNAME not set")
    if not self.REDIS_REFRESH_USER_USERNAME: raise RuntimeError("REDIS_REFRESH_USER_USERNAME not set")
    if not self.REDIS_SESSION_USER_PASSWORD: raise RuntimeError("REDIS_SESSION_USER_PASSWORD not set")
    if not self.REDIS_REFRESH_USER_PASSWORD: raise RuntimeError("REDIS_REFRESH_USER_PASSWORD not set")

    self.REDIS_SESSION_USER = redis.Redis(
      host = self.REDIS_HOST,
      port = int(self.REDIS_PORT),
      username = self.REDIS_SESSION_USER_USERNAME,
      password = self.REDIS_SESSION_USER_PASSWORD
    )

    self.REDIS_REFRESH_USER = redis.Redis(
      host = self.REDIS_HOST,
      port = int(self.REDIS_PORT),
      username = self.REDIS_REFRESH_USER_USERNAME,
      password = self.REDIS_REFRESH_USER_PASSWORD
    )

  async def get_session_token_id(self, email: str, refresh_token: str) -> tuple[int, str | int]:
    """
    Checks if **refresh_token** is valid and returns its id

    Args:
      email (str): The email against whome the **refresh_token** is to be compaired
      refresh_token (str): The **refresh_token** that is to be compaired

    Returns:
      tuple[int, int]:
        (1, "message") if **email** is invalid or **refresh_token** is not provided,
        (0, id) if **refresh_token** is valid,
        (1, "False") if **refresh_token** is not valid,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email): return (1, "Provide a valid email")
    if not refresh_token: return (1, "Provide a refresh_token")

    async for token in self.REDIS_REFRESH_USER.scan_iter(f"refresh:{email}:*:refresh_token"):
      try:
        val = await self.REDIS_REFRESH_USER.get(token)
        if isinstance(val, bytes) and hashlib.sha256(refresh_token.encode()).digest() == val:
          return (0, token)
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "False")

  async def is_refresh_token_valid(self, email: str, refresh_token: str) -> tuple[int, str]:
    """
    Checks if **session_token** is valid

    Args:
      email (str): The email against whome the **refresh_token** is to be compaired
      refresh_token (str): The **session_token** that is to be compaired

    Returns:
      tuple[int, str]:
        (1, "message") if **email** is invalid or **refresh_token** is not provided,
        (0, "True") if **session_token** is valid,
        (1, "False") if **session_token** is not valid,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email): return (1, "Provide a valid email")
    if not refresh_token: return (1, "Provide a refresh_token")

    async for token in self.REDIS_REFRESH_USER.scan_iter(f"refresh:{email}:*:refresh_token"):
      try:
        val = await self.REDIS_SESSION_USER.get(token)
        if isinstance(val, bytes) and hashlib.sha256(refresh_token.encode()).digest() == val:
          return (0, "True")
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "False")

  async def is_session_token_valid(self, email: str, session_token: str) -> tuple[int, str]:
    """
    Checks if **session_token** is valid

    Args:
      email (str): The email against whome the **refresh_token** is to be compaired
      refresh_token (str): The **session_token** that is to be compaired

    Returns:
      tuple[int, str]:
        (1, "message") if **email** is invalid or **refresh_token** is not provided,
        (0, "True") if **session_token** is valid,
        (1, "False") if **session_token** is not valid,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email): return (1, "Provide a valid email")
    if not session_token: return (1, "Provide a session_token")

    async for token in self.REDIS_SESSION_USER.scan_iter(f"session:{email}:*"):
      try:
        val = await self.REDIS_SESSION_USER.get(token)
        if isinstance(val, bytes) and hashlib.sha256(session_token.encode()).digest() == val:
          return (0, "True")
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "False")

  async def add_refresh_token_entry(self, email: str) -> tuple[int, str]:
    """
    Adds a new **refresh_token** for the provided **email**

    Args:
      email (str): The email for which the **refresh_token** is to be created

    Returns:
      tuple[int, str]:
        (1, "message") if **email** is invalid or number of pre existing **refresh_token** exceed **self.MAX_ALLOWED_REFRESH_TOKENS**,
        (0, refresh_token) if successful,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email):
      return (1, "Provide a valid email")

    refresh_token: str = secrets.token_urlsafe(self.REFRESH_TOKEN_LENGTH)
    hashed_refresh_token: bytes = hashlib.sha256(refresh_token.encode()).digest()

    for i in range(self.MAX_ALLOWED_REFRESH_TOKENS):
      try:
        val = await self.REDIS_REFRESH_USER.get(f"refresh:{email}:{i}:refresh_token")
        if not val:
          await self.REDIS_REFRESH_USER.setex(name = f"refresh:{email}:{i}:refresh_token", value = hashed_refresh_token, time = self.REFRESH_TOKEN_EXPIRY)
          return (0, refresh_token)
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "Too many refresh_tokens")

  async def add_session_token_entry(self, email: str, refresh_token) -> tuple[int, str]:
    """
    Adds a new **session_token** for the provided **email** which is linked to the provided **refresh_token**, the refresh_token is validated

    Args:
      email (str): The email for which the **session_token** is to be created
      refresh_token (str): The **refresh_token** which issued the **session_token**, this is validated

    Returns:
      tuple[int, str]:
        (1, "message") if **email** or **refresh_token** is invalid or number of pre existing **session_token** exceed **self.MAX_ALLOWED_SESSION_TOKENS**,
        (0, session_token) if successful,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email):
      return (1, "Provide a valid email")

    refresh_token_id: str = ""

    val = await self.get_session_token_id(email, refresh_token)
    if val[0] == -1:
      return (-1, str(val[1]))
    elif val[0] == 1:
      if val[1] == "False":
        return (1, "Invalid refresh_token")
      else:
        return (1, "Provide a valid email")
    elif val[0] == 0:
      refresh_token_id = str(val[1])

    session_token: str = secrets.token_urlsafe(self.SESSION_TOKEN_LENGTH)
    hashed_session_token: bytes = hashlib.sha256(session_token.encode()).digest()

    for i in range(self.MAX_ALLOWED_SESSION_TOKENS):
      try:
        val = await self.REDIS_SESSION_USER.get(f"session:{email}:{i}")
        if not val:
          await self.REDIS_SESSION_USER.setex(
            name = f"session:{email}:{i}",
            value = hashed_session_token,
            time = self.SESSION_TOKEN_EXPIRY
          )
          await self.REDIS_REFRESH_USER.setex(
            name = f"refresh:{email}:{refresh_token_id}:sessions:{i}",
            value = f"session:{email}:{i}",
            time = self.SESSION_TOKEN_EXPIRY
          )
          return (0, session_token)
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "Too many session_tokens")

  async def remove_user_session(self, email: str, refresh_token: str) -> tuple[int, str]:
    """
    Removes both the given **refresh_token** and its corresponding **session_token** for the given email if the **refresh_token** is valid

    Args:
      email: The email for whom the **refresh_token** and **session_token** are to be removed
      refresh_token: The refresh_token that is verified, this is also deleted

    Returns:
      tuple[int, str]:
        (0, "Success") if successful,
        (1, "message") if **email** or **refresh_token** is not valid,
        (-1, "message") if an error happened
    """

    if not validations.is_valid_email(email):
      return (1, "Provide a valid email")

    val = await self.get_session_token_id(email, refresh_token)
    if val[0] != 0:
      return (1, "refresh_token is invalid")

    for i in range(self.MAX_ALLOWED_REFRESH_TOKENS):
      try:
        res = await self.REDIS_REFRESH_USER.get(f"refresh:{email}:{i}:refresh_token")
        if isinstance(res, bytes) and hashlib.sha256(refresh_token.encode()).digest() == res:
          async for token in self.REDIS_REFRESH_USER.scan_iter(f"refresh:{email}:{i}:sessions:*"):
            await self.REDIS_REFRESH_USER.delete(token)

          await self.REDIS_REFRESH_USER.delete(f"refresh:{email}:{i}:refresh_token")
          return (0, "Success")
      except Exception as e:
        self.logger.error(str(e))
        return (-1, str(e))

    return (1, "Provide a refresh_token")
