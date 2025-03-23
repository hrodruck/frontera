from game import Game
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
import json
import asyncio
import uvicorn

app = FastAPI()

origins = [os.getenv('MAIN_SERVER_IP', 'http://localhost')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartGameData(BaseModel):
    session_id: str
    player_id: str

class CommandData(BaseModel):
    command: str
    session_id: str
    player_id: str

class SessionData(BaseModel):
    session_id: str
    player_id: str

# Game session management
games = {}
game_progress = {}
locks = {}
buffered_player_commands = {}
is_processing_locks = {}
player_commands_lock = asyncio.Lock()
game_responses_per_player = {}

# Load zones data at startup
def load_zones():
    try:
        with open('data/zones.json', 'r') as f:
            zones_data = json.load(f)
            print(f"Loaded zones: {list(zones_data['zones'].keys())}")
            return zones_data
    except Exception as e:
        print(f"Error loading zones.json: {e}")

zones_data = load_zones()

async def get_game_from_session(session_id: str):
    return games.get(session_id)

async def new_session(session_id: str, game: Any):
    games[session_id] = game
    game_progress[session_id] = ''
    locks[session_id] = asyncio.Lock()
    buffered_player_commands[session_id] = {}
    game_responses_per_player[session_id] = {}
    is_processing_locks[session_id] = asyncio.Lock()
    asyncio.create_task(game_update(session_id))
    asyncio.create_task(poll_game_progress(session_id))

async def poll_game_progress(session_id: str):
    while True:
        try:
            async with locks[session_id]:
                updates = []
                async for item in games[session_id].get_progress_queue():
                    updates.append(item)
                game_progress[session_id] += ''.join(updates)
            await asyncio.sleep(0.2)
        except RuntimeError:
            break

async def get_game_progress(session_id: str):
    if session_id in locks:
        async with locks[session_id]:
            progress = game_progress[session_id]
            game_progress[session_id] = ''
            return progress
    return ''

async def game_update(session_id):
    game = await get_game_from_session(session_id)
    while True:
        try:
            async with is_processing_locks[session_id]:
                async with player_commands_lock:
                    player_commands = buffered_player_commands[session_id]
                    buffered_player_commands[session_id] = {}
                async for player_id, game_response in game.process_player_commands(player_commands):
                    game_responses_per_player[session_id][player_id] = game_response
            await asyncio.sleep(0.1)
        except RuntimeError:
            break

async def get_player_progress(session_id, player_id):
    if game_responses_per_player and player_id in game_responses_per_player.get(session_id):
        player_response = game_responses_per_player[session_id][player_id]
        game_responses_per_player[session_id][player_id] = ''
        return player_response
    return ''

# Endpoints
@app.post("/api/game-progress")
async def game_progress_endpoint(data: SessionData):
    session_id = data.session_id
    progress = await get_game_progress(session_id)
    return JSONResponse(content={"status": "success", "response": progress})

@app.post("/api/player-progress")
async def player_responses_endpoint(data: SessionData):
    session_id = data.session_id
    player_id = data.player_id
    progress = await get_player_progress(session_id=session_id, player_id=player_id)
    return JSONResponse(content={"status": "success", "response": progress})

@app.post("/api/process-input")
async def process_input(data: CommandData):
    session_id = data.session_id
    player_id = data.player_id
    if session_id not in buffered_player_commands:
        response = "You are somehow sending commands to a non-existing game!"
    else:
        async with player_commands_lock:
            buffered_player_commands[session_id][player_id] = data.command
        response = "Your command was recorded and will be executed soon!"
    return JSONResponse(content={"status": "success", "response": response})

@app.post("/api/start-game")
async def start_game(data: StartGameData):
    try:
        session_id = data.session_id
        player_id = data.player_id
        game = await get_game_from_session(session_id)
        if not game:
            game = Game()
            await new_session(session_id, game)
            await game.set_all_zones(zones_data)
            default_zone = zones_data.get("defaultZone")        
            default_subzone = zones_data.get("defaultSubzone")
            print(f"Starting game for session {session_id}, player {player_id} at {default_zone}/{default_subzone}")
            await game.start_game(zone=default_zone, subzone=default_subzone)
            await game.add_player(player_id, default_zone, default_subzone)
            return JSONResponse(content={"status": "success", "message": "New game started!"})
        else:
            # Add player with default location
            default_zone = zones_data.get("defaultZone")        
            default_subzone = zones_data.get("defaultSubzone")
            zone_data = zones_data["zones"].get(default_zone)
            subzone_data = zone_data.get("subzones").get(default_subzone)
            await game.add_player(player_id, default_zone, default_subzone)
            print(f"Starting game for session {session_id}, player {player_id} at {default_zone}/{default_subzone}")
            return JSONResponse(content={"status": "success", "message": "Player added to existing game!"})
    except Exception as e:
        print(f"Error in start_game: {e}")
        return JSONResponse(content={"status": "error", "message": "Could not start new game, please try again."})

async def serve():
    port_number = int(os.getenv('GAME_SERVER_PORT_NUMBER', 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port_number)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(serve())