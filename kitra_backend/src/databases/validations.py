from email_validator import validate_email, EmailNotValidError
from google.oauth2 import id_token
from google.auth.transport import requests

import os
import logging

logger = logging.getLogger(__name__)

def is_valid_email(email: str) -> bool:
  try:
    validate_email(email)
    return True
  except EmailNotValidError:
    return False

def validate_JWT_token(token: str):
  webClientId: str = os.environ.get("GOOGLE_WEB_CLIENT_ID", "")
  if not webClientId:
    raise RuntimeError("GOOGLE_WEB_CLIENT_ID not set")

  try:
    info: dict[str, str] = id_token.verify_oauth2_token(token, requests.Request(), webClientId)

  except ValueError:
    return (401, "Invalid JWT_token")

  except Exception as e:
    logger.error(f"Unable to autherise JWT: {e}")
    return (500, f"Unable to autherise JWT: {e}")

  return (0, info)
