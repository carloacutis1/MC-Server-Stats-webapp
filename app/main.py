from fastapi import FastAPI, HTTPException, Path, Request

import os
import re
from contextlib import asynccontextmanager
import aiomcrcon  # RCON client used to talk to the Minecraft server

# Connection settings for the Minecraft server's RCON interface
RCON_HOST = os.environ.get("RCON_HOST")
RCON_PORT = int(os.environ.get("RCON_PORT"))
# Read from the environment so the password never lives in source control
RCON_PASS = os.environ.get("RCON_PASS")
if not RCON_PASS:
    raise RuntimeError("RCON_PASS environment variable is not set")

# define list of player names connected
names = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup: open a single shared RCON connection and stash it
    # on app.state so every request handler can reuse it instead of reconnecting.
    app.state.rcon = aiomcrcon.Client(RCON_HOST, RCON_PORT, RCON_PASS)
    try:
        await app.state.rcon.connect(10.0)
    except Exception:
        # Don't crash the whole API if the game server is unreachable at boot
        # just log it and let RCON-dependent routes fail individually later.
        print(f"Warning: could not connect to RCON at {RCON_HOST}:{RCON_PORT}")
    yield
    # Runs once on shutdown: close the RCON connection if it was ever established.
    if app.state.rcon._ready:
        await app.state.rcon.close()

# Create the FastAPI app, wiring in the lifespan handler above for startup/shutdown
app = FastAPI(lifespan=lifespan)

# helper function to get player data
async def get_entity_data(rcon, name : str, field : str) -> str:
    try:
        response, _ = await rcon.send_cmd(f"data get entity {name} {field}")
    except Exception:
        # RCON call failed (e.g. connection dropped) - surface as a bad gateway
        raise HTTPException(status_code=502, detail="Failed to reach Minecraft server")

    # if there the player is not online 
    if response == "No entity was found":
        raise HTTPException(status_code=404, detail="Player not found")

    match = re.search(r"entity data: (.+)", response)
    if not match:
        raise HTTPException(status_code=502, detail=f"Unexpected RCON response: {response}")

    return match.group(1)


# Basic sanity-check route
@app.get("/")
async def root():
    return {"message": "Hello World"}


# Fetches the Minecraft world seed by sending the "seed" console command over RCON
@app.get("/seed")
async def getSeed(request: Request):
    try:
        response, _ = await request.app.state.rcon.send_cmd("seed")
    except Exception:
        # RCON call failed (e.g. connection dropped) - surface as a bad gateway
        raise HTTPException(status_code=502, detail="Failed to reach Minecraft server")

    # RCON replies with text like "Seed: [12345]", so pull the number out of the brackets
    match = re.search(r"\[(-?\d+)\]", response)
    if not match:
        raise HTTPException(status_code=502, detail=f"Unexpected RCON response: {response}")

    # return the first capture group
    return {"seed": int(match.group(1))}

# get players online 
@app.get("/players/online")
async def getOnlinePlayers(request: Request):
    try:
        response, _ = await request.app.state.rcon.send_cmd("list")
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to reach Minecraft Server")

    # get the number of players online
    num_online = re.search(r"(\d?\d)", response)
    if not num_online:
        raise HTTPException(status_code=502, detail=f"Unexpected RCON response: {response}")

    num_online = num_online.group(1)
    # if there are players online, get all of their names
    if int(num_online) > 0:
        names = [re.search(r": (.+)", response)]
        if not names[0]:
            raise HTTPException(status_code=502, detail=f"Unexpected RCON response: {response}")

        names = names[0].group(1)

        # separate each name into elements of a list
        names = names.split(", ")

        # return the list of names 
        return {"Number of players online": num_online, "Connected Users": names}

    return "There are no players online."

# return a given player's health
@app.get("/players/{name}/health")
async def getPlayerHealth(request: Request, name: str = Path(pattern=r"^\w{1,16}$")):
    health = await get_entity_data(request.app.state.rcon, name, "Health")
    return {"message": health}

# return a given player's position
@app.get("/players/{name}/position")
async def getPlayerPos(request: Request, name: str = Path(pattern=r"^\w{1,16}$")):
    pos = await get_entity_data(request.app.state.rcon, name, "Pos")
    return {"message": pos}

# return a given player's hunger/food level
@app.get("/players/{name}/hunger")
async def getPlayerHunger(request: Request, name: str = Path(pattern=r"^\w{1,16}$")):
    hunger = await get_entity_data(request.app.state.rcon, name, "foodLevel")
    return {"message": hunger}

# return a given player's XP level
@app.get("/players/{name}/xp")
async def getPlayerXp(request: Request, name: str = Path(pattern=r"^\w{1,16}$")):
    xp = await get_entity_data(request.app.state.rcon, name, "XpLevel")
    return {"message": xp}
