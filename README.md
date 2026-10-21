# MC Server Stats

A small REST API that reports live stats from a Minecraft server: who is online, and each player's health, position, hunger and XP.

It's built with [FastAPI](https://fastapi.tiangolo.com/) and talks to the server over [RCON](https://minecraft.wiki/w/RCON), the remote console protocol built into Minecraft. No mods or plugins are needed. The API sends ordinary console commands (`list`, `seed`, `data get entity ...`) and turns the text replies into JSON.

## How it works

```
 HTTP client ──► FastAPI app ──RCON (port 25575)──► Minecraft server
   (curl,          app/main.py                         (vanilla, Paper, etc.)
    browser)
```

When the API starts, it opens one RCON connection and every request reuses it. If the Minecraft server can't be reached at startup, the API still starts. Requests that need RCON then return `502 Bad Gateway` until the server is reachable.

## Endpoints

| Method | Path | Returns |
| ------ | ---- | ------- |
| GET | `/` | Health check (`{"message": "Hello World"}`) |
| GET | `/seed` | The world seed |
| GET | `/players/online` | Number of players online and their names |
| GET | `/players/{name}/health` | Player's health (0–20) |
| GET | `/players/{name}/position` | Player's `[x, y, z]` coordinates |
| GET | `/players/{name}/hunger` | Player's food level (0–20) |
| GET | `/players/{name}/xp` | Player's XP level |

`{name}` must be a valid Minecraft username (1–16 letters, digits or underscores). The player endpoints return `404` if that player isn't online.

The API also generates interactive docs, which you can use to try every endpoint from your browser:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example

```bash
$ curl http://localhost:8000/players/online
{"Number of players online":"2","Connected Users":["Steve","Alex"]}

$ curl http://localhost:8000/players/Steve/position
{"message":"[-112.5d, 64.0d, 238.3d]"}
```

## Prerequisites

- **A Minecraft Java server with RCON enabled.** Set these in the server's `server.properties` and restart it:
  ```properties
  enable-rcon=true
  rcon.password=your-secret-password
  rcon.port=25575
  ```
  RCON uses its own port, separate from the game port players join on (25565 by default). Make sure the server's firewall allows the RCON port from the machine running this API.
- **Either** Docker with Docker Compose (recommended), **or** Python 3.12.

## Configuration

The app is configured with environment variables. Copy the example file and edit it:

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `RCON_HOST` | Yes | — | Hostname or IP of the Minecraft server, e.g. `10.40.0.100` |
| `RCON_PASS` | Yes | — | Must match `rcon.password` on the server. The app won't start without it. |
| `RCON_PORT` | No | `25575` | Must match `rcon.port` on the server. This is **not** the game port (25565). |

`.env` is git-ignored, so your password stays out of the repo.

## Running

### With Docker Compose (recommended)

```bash
docker compose up --build
```

The API is now at http://localhost:8000 and connects to the server set by `RCON_HOST` in `.env`.

The `app/` folder is mounted into the container with auto-reload turned on, so code changes apply without a rebuild. Changes to `.env` are not picked up automatically. After editing it, run `docker compose up -d` to recreate the container; `docker compose restart` keeps the old values.

### Without Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export RCON_PASS=your-secret-password
export RCON_HOST=localhost   # or the server's IP
export RCON_PORT=25575

uvicorn app.main:app --reload
```

The API is now at http://localhost:8000.

## Troubleshooting

- **`RuntimeError: RCON_PASS environment variable is not set`**: Create `.env` (Docker) or export `RCON_PASS` (local) before starting the app.
- **`Warning: could not connect to RCON at ...` / endpoints return 502**: Check that the Minecraft server is running, that RCON is enabled, and that the host, port and password match. Make sure `RCON_PORT` is the RCON port (25575), not the game port (25565). If the server started after the API, restart the API.
- **Connection times out**: The machine running the API can't reach the server. Test with `nc -vz <host> 25575` (Linux/WSL) or `Test-NetConnection <host> -Port 25575` (Windows PowerShell). If Windows can reach the server but WSL can't, for example over a VPN, turn on WSL mirrored networking: add `networkingMode=mirrored` under `[wsl2]` in `C:\Users\<you>\.wslconfig`, then run `wsl --shutdown`.
- **Player endpoints return 404 / `/players/online` is empty while you're logged in**: The API is probably connected to a different server than the one you're on. Check that `RCON_HOST` is the same address you join in Minecraft. Otherwise the player isn't online right now, or the name is misspelled.

## Roadmap

- Ingest server log events (joins, leaves, starts, stops) and store them in a database
- Player history and playtime endpoints
- Notifications (Discord, ntfy, etc.) on server events
- API key authentication
- Tests and CI with GitHub Actions
