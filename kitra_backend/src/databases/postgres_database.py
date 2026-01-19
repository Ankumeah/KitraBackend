from psycopg_pool import AsyncConnectionPool

import os
import logging

from .error import Error

class Database:
  logger = logging.getLogger(__name__)

  ADD_USER_QUERY: str = "INSERT INTO users (email) VALUES (%s);"
  IS_EMAIL_IN_DATABASE_QUERY: str = "SELECT email FROM users WHERE email = %s;"
  ADD_MESSAGE_QUERY: str = "INSERT INTO messages (sender, receiver, content) VALUES (%s, %s, %s) RETURNING (timestamp);"
  GET_NEW_MESSAGES_QUERY: str = "SELECT * FROM messages WHERE ((sender = %(user_a)s AND receiver = %(user_b)s) OR (sender = %(user_b)s AND receiver = %(user_a)s)) AND (timestamp > %(timestamp)s) ORDER BY timestamp;"
  GET_ID_FROM_EMAIL_QUERY: str = "SELECT id FROM users WHERE email = %s"

  def __init__(self):
    try:
      self.POSTGRES_HOST = os.environ["POSTGRES_HOST"]
      self.POSTGRES_PORT = os.environ["POSTGRES_PORT"]
      self.POSTGRES_DB = os.environ["POSTGRES_DB"]
      self.POSTGRES_USER = os.environ["POSTGRES_USER"]
      self.POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
    except KeyError as e:
      raise RuntimeError(f"{e.args[0]} not set")

    self.CONNINFO: str = f"""
      host={self.POSTGRES_HOST}
      port={self.POSTGRES_PORT}
      dbname={self.POSTGRES_DB}
      user={self.POSTGRES_USER}
      password={self.POSTGRES_PASSWORD}
    """

  async def _execute(self, query, params: tuple = (), commit: bool = False) -> list | Error:
    """
    Use this interface to execute queries to the postgres database (only for internal use)

    Args:
      query (str): This is the SQL query that is to be executed. Use %s for placeholders
      params (tuple, optional): Use this to pass the variables for the query's placeholders. Defaults to ()
      commit (bool, optional): This specifies whether or not to commit the query. Defaults to False

    Returns:
      tuple[int, list]:
        (0, fetchall) if the query returned something,
        (1, [str(e)]) if error

    Raises:
      RuntimeError: If connection pool is not initalise
    """

    try:
      if not self.POSTGRES_POOL:
        raise RuntimeError("connection pool is not initialized, run Database.init() to initalise it")

      async with self.POSTGRES_POOL.connection() as conn:
        async with conn.cursor() as cur:
          await cur.execute(query, params)
          if cur.description:
            res = await cur.fetchall()
          else:
            res = []

          if commit:
            await conn.commit()

    except Exception as e:
      self.logger.error(str(e))
      return Error(error = str(e))

    return res

  async def init_db(self) -> tuple[int, str]:
    """
    Initializes the connection pool

    Args:
      None

    Returns:
      tuple[int, str]:
        (0, "Success") if successful,
        (1, str(e)) if error
    """

    try:
      self.POSTGRES_POOL = AsyncConnectionPool(
        conninfo = self.CONNINFO,
        min_size = 1,
        max_size = 10,
        open = False
      )

      await self.POSTGRES_POOL.open()

    except Exception as e:
      self.logger.error(str(e))
      return (1, str(e))

    return (0, "Success")

  async def add_user(self, email: str) -> None | Error:
    """
    Adds a new entry to the **users** table of the postgres database. No build in checks are performed except the database's own constraints

    Args:
      username (str): Username of the user. Is not unique in the database
      email (str): Email of the user. Is unique in the database

    Returns:
      tuple[int, str]:
        (0, "Success") if successful,
        (1, str(e)) if error
    """

    res = await self._execute(self.ADD_USER_QUERY, (email.lower(),), commit = True)

    if isinstance(res, Error):
      return res

  async def is_email_in_database(self, email: str) -> bool | Error:
    """
    Checks if an **email** is in the postgres database

    Args:
      email (str): The email to be checked

    Returns:
      tuple[int, list]:
        (0, [ans (bool)]) if successful,
        (1, [str(e)]) if error
    """

    res = await self._execute(self.IS_EMAIL_IN_DATABASE_QUERY, (email.lower(),))

    if isinstance(res, Error):
      return res

    if res[1]:
      return True
    else:
      return False

  async def get_id_from_email(self, email: str) -> int | Error:
    """
    Returns the **id** matched with an **email** in the postgres database

    Args:
      email (str): The email whose id is to be returned

    Returns:
      tuple[int, list]:
        (1, ["messages"]) if no email is provided or the email is not in the database,
        (1, [str(e)]) if error,
        (0, [id (int)]) if successful
    """

    res = await self.is_email_in_database(email.lower())
    if isinstance(res, Error):
      return res
    elif not res:
      return Error(error = f"{email} is not a valid user")

    res = await self._execute(self.GET_ID_FROM_EMAIL_QUERY, (email.lower(),))
    if isinstance(res, Error):
      return res

    return res[1][0][0]

  async def send_message(self, sender_email: str, receiver_email: str, content: str) -> int | Error:
    """
    Add a new message to the **messages** table and returns its timestamp

    Args:
      sender_email (str): The email of the sender
      receiver_email (str): The email of the receiver
      content (str): The content of the message to be added

    Returns:
      tuple[int, tuple[int, str] | int]:
        (0, (timestamp, content)) if successful,
        (1, 1) if either of the users are not in the database,
        (-1, -1) if error
    """

    res = await self._execute(self.GET_ID_FROM_EMAIL_QUERY, (sender_email.lower(),))
    if isinstance(res, Error):
      return -1
    elif not res[1]:
      return -2

    sender_id: int = res[1][0][0]

    res = await self._execute(self.GET_ID_FROM_EMAIL_QUERY, (receiver_email.lower(),))
    if isinstance(res, Error):
      return -1
    elif not res[1]:
      return -2

    receiver_id: int = res[1][0][0]

    res = await self._execute(self.ADD_MESSAGE_QUERY, (sender_id, receiver_id, content))
    if isinstance(res, Error):
      return -1

    timestamp: int = int(res[1][0][0].timestamp() // 1)

    return timestamp

  async def get_new_messages(self, email: str, last_message: int) -> list | Error:
    ...
