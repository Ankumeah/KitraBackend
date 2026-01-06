from fastapi import WebSocket

class WebSocketManager:
  def __init__(self):
    self._conn_dict: dict[str, dict[WebSocket, str]] = {}
    "{client_email: {WebSocket: session_token}}"

  def add_connection(self, client: WebSocket, client_email: str, session_token: str):
    self._conn_dict.setdefault(client_email, {})[client] = session_token

  def remove_connection(self, client_email: str, client: WebSocket):
    if not self._conn_dict.get(client_email, ""):
      return
    if not self._conn_dict.get(client_email, {}).get(client):
      return

    self._conn_dict.get(client_email, {}).pop(client)

    if not self._conn_dict.get(client_email, {}):
      self._conn_dict.pop(client_email)

  def is_duplicate_session(self, client_email: str, session_token: str) -> bool:
    if session_token not in self._conn_dict.get(client_email, {}).values():
      return False
    return True

  def get_clients(self, client_email: str):
    return self._conn_dict.get(client_email, {}).keys()

  async def remove_all_clients(self):
    for email in self._conn_dict.values():
      for client in email.keys():
        await client.close()

    self._conn_dict.clear()
