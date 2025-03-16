from game import Game
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import os
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

class RoomData(BaseModel):
    room: Dict[str, Any]
    session_id: str
    player_id: str

class CommandData(BaseModel):
    command: str
    session_id: str
    player_id: str
    
class SessionData(BaseModel):
    session_id: str
    player_id: str

# This session management is simplified since it's only for Game processing
games = {}
game_progress = {}
locks = {}
buffered_player_commands = {}
is_processing_locks = {}
player_commands_lock = asyncio.Lock()
game_responses_per_player = {}

async def get_game_from_session(session_id: str):
    if session_id in games.keys():
        return games[session_id]
    else:
        return None
    
async def new_session(session_id: str, game: Any):
    games[session_id] = game #this is stored indefinetely in memory for now
    game_progress[session_id]=''
    locks[session_id] = asyncio.Lock()
    buffered_player_commands[session_id]={}
    game_responses_per_player[session_id]={}
    is_processing_locks[session_id] = asyncio.Lock()
    asyncio.create_task(game_update(session_id))
    asyncio.create_task(poll_game_progress(session_id))

async def poll_game_progress(session_id:str):
    while True:
        try:
            async with locks[session_id]:
                updates = []
                async for item in games[session_id].get_progress_queue():
                    updates.append(item)
                game_progress[session_id] += (''.join(updates))
            await asyncio.sleep(0.2)
        except RuntimeError as e:
            break

async def get_game_progress(session_id:str): # this function helps return game progress from this server to the response
    if session_id in locks.keys():
        async with locks[session_id]:
            progress = game_progress[session_id]
            game_progress[session_id]=''
            return progress
    else:
        return ''

async def game_update(session_id):
    game = await get_game_from_session(session_id)
    while True:
        try:
            async with is_processing_locks[session_id]:
                async with player_commands_lock:
                    player_commands = buffered_player_commands[session_id]
                    buffered_player_commands[session_id] = {}
                    #player_commands['GameMaster'] = "I do nothing and wait"
                async for player_id, game_response in game.process_input(player_commands):
                    game_responses_per_player[session_id][player_id] = game_response
            await asyncio.sleep(0.1)
        except RuntimeError as e:
            break

async def get_player_progress(session_id, player_id):
    if player_id in game_responses_per_player[session_id].keys():
        player_response = game_responses_per_player[session_id][player_id]
        game_responses_per_player[session_id][player_id] = ''
        return player_response
    else:
        return ''

#endpoints
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
    game = await get_game_from_session(session_id)
    player_id = data.player_id
    if session_id not in buffered_player_commands:
        response = "You are somehow sending commands a non-existing game!"
    elif player_id not in buffered_player_commands[session_id].keys():
        async with player_commands_lock:
            buffered_player_commands[session_id][player_id] = data.command
        response = "Your command was recorded and will be executed soon!"
    else:
        response = "You already have a command waiting!"
    return JSONResponse(content={"status": "success", "response": response})
    

@app.post("/api/start-game")
async def start_game(data: RoomData):
    try:
        session_id = data.session_id
        game = await get_game_from_session(session_id)
        if not game:
            game = Game() #start a new instance anyways, since the player could be restarting their game
            await new_session(session_id, game)
            room = data.room
            room_description = room['description']
            room_description.pop('customObjects', None) #weirdness from the frontend regarding custom rooms
            room_description.pop('winning_message', None)
            room_description.pop('losing_message', None)
            room_description.pop('room_description', None)
            game.set_scene(room_description, room['winning_message'], room['losing_message'])
            print(f"{session_id=}")
            await game.start_game()
            response = JSONResponse(content={"status": "success", "message": "New game started!"})
        else:
            response = JSONResponse(content={"status": "success", "message": "This game is already running!"})
        return response
    except Exception as e:
        print(e)
        return JSONResponse(content={"status": "error", "message": "Could not start new game, please try again."})

async def serve():
    port_number = int(os.getenv('GAME_SERVER_PORT_NUMBER'))
    config = uvicorn.Config(app, host="0.0.0.0", port=port_number)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(serve())
    
# Note: This server only needs to manage game state, not room selection or session creation