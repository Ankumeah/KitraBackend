# Old commit history

When making this project, I accidently did the ultra biggner mistake of pushing my API keys (webClientID) to github.
The keys ended up in several commits before i noticed and so I made the decision on nukeing the old repo and making a new one.
In an attempt to preserve the only proof my progress, I am copying the old repo's log and placing it here.

```text
9ced9a8 (HEAD -> master, origin/master, origin/HEAD) fixed bug where every websocket would disconnect after the first message
8298240 fixed bug in kitra_backend/src/wss/exchange_messages.py where the Response class was json dumped twice
df3f5e0 renamed .env/ and .env.example/ to .env.d/ and .env.d.example/, fixed send_message() in kitra_backend/src/databases/postgres_database.py, fixed kitra_backend/src/databases/websocket_manager.py, fixed receving messages in kitra_backend/src/wss/exchange_messages.py, notifying client is still untested
84eba4f Updated REDME.md to include flake8 badge
97daaca seprated refresh_token to diffrent redis user, db init now executes a single numbered file in db_init/version/, added untested experimatal messeging through websockets, added github actions for auto linting with flake8 (This will be the first test, fingers crossed)
0a655a2 spilt all coustom images into their own dir, split the main backed into api/ and ws/ to accomadate for ws being bound by a single worker, moved db init logic into ./db_init/, added nginx, added ./.env.example which containes files with empty vars for every env var that has to be filled
e298637 updated to psycopg3, using async psycopg and redis, /api/is_valid_user is now a GET endpoint, removed more accidental pycache
01bf822 removed accidental __pycache__
6c0369e switched to fastapi in places of flask, routes and database files are now packaged in src/apis/ and src/databases respectively, docker compose now gets env vars from .env directly
675ecb2 (origin/main) using hashlib sha256 to hash refresh tokens insed of bccrypt, the default name for key.pem and cert.pem is now .key.pem and .cert.pem, added new route /api/is_valid_user and /api/send_message (untested)
5ca00e6 added new route /api/logout to logout, refresh_tokens are now hashed
8a1c0f0 fixed bugs with session and refresh token creation, redis's and postgres's ports are no longer public
843f3c6 JWT is now varified and a session and refresh token along with their expire time are returned, new user is added if needed
ba2485e the server uses https (provided cret.pem and key.pem) are in ./, src/database.py moved to src/postgres_database.py, redis databse logic is in src/redis_database.py, added doc strings in src/postgres_database.py, username in the postgres databse is not unique
98a27b4 commented out REDIS_CACHE_USER to add support for render
9b91d0b changed maxmemory of redis from 2GB to 128MB to fit within render
6bb0a49 removed start.sh and run.sh, added connection support for redis
4f7ed5f fixed mismatched log message in src/validation.py
88bf5fa the docker images now uses gunicorn to deploy insted of the flask dev server
3c05087 useing postgres insted of sqlite3, added docker-compose.yaml
95835bf added Dockerfile and moved is_valid_email() and validate_registeration_credientials() into src/validition.py
559905a inital commit: has basic user sign up
```
