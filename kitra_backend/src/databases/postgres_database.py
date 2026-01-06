from psycopg_pool import AsyncConnectionPool

import os
import logging

class Database:
  logger = logging.getLogger(__name__)

  ADD_USER_QUERY: str = "INSERT INTO users (email) VALUES (%s);"
  IS_EMAIL_IN_DATABASE_QUERY: str = "SELECT email FROM users WHERE email = %s;"
  ADD_MESSAGE_QUERY: str = "INSERT INTO messages (sender, receiver, content) VALUES (%s, %s, %s) RETURNING (timestamp);"
  GET_MESSAGES_QUERY: str = "SELECT * FROM messages WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s) ORDER BY timestamp;"
  GET_ID_FROM_EMAIL_QUERY: str = "SELECT id FROM users WHERE email = %s"

  def __init__(self):
    self.POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "")
    self.POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "")
    self.POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "")
    self.POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "")
    self.POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "")

    if not self.POSTGRES_HOST: raise RuntimeError("POSTGRES_HOST not set")
    if not self.POSTGRES_PORT: raise RuntimeError("POSTGRES_PORT not set")
    if not self.POSTGRES_DB: raise RuntimeError("POSTGRES_DB not set")
    if not self.POSTGRES_USER: raise RuntimeError("POSTGRES_USER not set")
    if not self.POSTGRES_PASSWORD: raise RuntimeError("POSTGRES_PASSWORD not set")

    self.CONNINFO: str = f"""
      host={self.POSTGRES_HOST}
      port={self.POSTGRES_PORT}
      dbname={self.POSTGRES_DB}
      user={self.POSTGRES_USER}
      password={self.POSTGRES_PASSWORD}
    """

  async def _execute(self, query, params: tuple = (), commit: bool = False) -> tuple[int, list]:
    """
    Use this interface to execute queries to the postgres database (only for internal use)

    Args:
      query (str): This is the SQL query that is to be executed. Use %s for placeholders
      params (tuple, optional): Use this to pass the variables for the query's placeholders. Defaults to ()
      commit (bool, optional): This specifies whether or not to commit the query. Defaults to False

    Returns:
      tuple[int, list]:
        (0, fetchall) if commit is False,
        (1, [str(e)]) if error
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
      return (1, [str(e)])

    return (0, res)

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

  async def add_user(self, email: str) -> tuple[int, str]:
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

    if res[0] != 0:
      return (1, res[1][0])

    return (0, "Success")

  async def is_email_in_database(self, email: str) -> tuple[int, list]:
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

    if res[0] != 0:
      return res

    if res[1]:
      return (0, [True])
    else:
      return (0, [False])

  async def get_id_from_email(self, email: str) -> tuple[int, list]:
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
    if res[0] != 0:
      return res
    elif not res[1][0]:
      return (1, [f"{email} is not a valid user"])

    res = await self._execute(self.GET_ID_FROM_EMAIL_QUERY, (email.lower(),))
    if res[0] != 0:
      return res
    return (0, res[1][0][0])

  async def send_message(self, sender_email: str, receiver_email: str, content: str) -> tuple[int, int]:
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
    if not res[1]:
      return (1, 1)
    if res[0] != 0:
      return (-1, -1)

    sender_id: int = res[1][0][0]

    res = await self._execute(self.GET_ID_FROM_EMAIL_QUERY, (receiver_email.lower(),))
    if not res[1]:
      return (1, 1)
    if res[0] != 0:
      return (-1, -1)

    receiver_id: int = res[1][0][0]

    res = await self._execute(self.ADD_MESSAGE_QUERY, (sender_id, receiver_id, content))
    if res[0] != 0:
      return (-1, -1)

    timestamp: int = int(res[1][0][0].timestamp() // 1)

    return (0, timestamp)
