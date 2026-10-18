from fastapi import FastAPI, HTTPException, Request

import re
from contextlib import asynccontextmanager
import aiomcrcon  # RCON client used to talk to the Minecraft server

# Connection settings for the Minecraft server's RCON interface
RCON_HOST = "10.40.0.100"
RCON_PORT = 25575
RCON_PASS = "carlo"

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
        print(f"Warning: could not connect to RCON at {RCON_HOST}:{RCON_PORT}; /seed will be unavailable")
    yield
    # Runs once on shutdown: close the RCON connection if it was ever established.
    if app.state.rcon._ready:
        await app.state.rcon.close()

# Create the FastAPI app, wiring in the lifespan handler above for startup/shutdown
app = FastAPI(lifespan=lifespan)


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


# TODO: not implemented yet - should return the list of online players
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

# return all of a player's info
@app.get("/players/{name}")
async def getPlayerStats(name: str, request: Request):
    try:
        response, _ = await request.app.state.rcon.send_cmd("data get entity {name}")
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to reach Minecraft Server")

    # if there the player is not online 
    if response = "No entity was found":
        raise HTTPException(status_code=404, detail="Player not found")
    
    
    return {"message": }

# return a given player's health
@app.get("/players/{name}/health")
async def getPlayerHealth(name: str, reguest: Request):
    return {"message": "Player Health"}

# TODO: not implemented yet - should return a given player's position
@app.get("/players/{name}/position")
async def getPlayerPos():
    return {"message": "Players Online"}

# TODO: not implemented yet - should return a given player's hunger/food level
@app.get("/players/{name}/hunger")
async def getPlayerHunger():
    return {"message": "Player Hunger"}

# TODO: not implemented yet - should return a given player's XP level
@app.get("/players/{name}/xp")
async def getPlayerXp():
    return {"message": "Player xp"}
