import asyncio
import json
import copy
import os
import re
import random
import aiofiles
from engine_game_object import EngineGameObject
from game_object import GameObject

class Game():

    def __init__(self):
        self.game_ended = False
        self.game_progress_queue = ''
        self.progress_lock = asyncio.Lock()
        self.game_objects = {}
        self.engine_game_object = None
        self.async_gameobject_init = None
        self.active_players = set()
        print("Engine is running. Use set_scene and start_game!")

    async def get_progress_queue(self):
        if not self.game_ended:
            async with self.progress_lock:
                if self.engine_game_object is not None:
                    async for item in self.engine_game_object.get_progress_queue():
                        self.game_progress_queue += item
                        yield self.game_progress_queue
                        self.game_progress_queue = ''
                        await asyncio.sleep(0.02)
                for k, v in self.game_objects.items():
                    async for item in self.game_objects[k].get_progress_queue():
                        self.game_progress_queue += item
                        yield self.game_progress_queue
                        self.game_progress_queue = ''
                        await asyncio.sleep(0.02)
        else:
            raise StopAsyncIteration
        
    async def add_to_progress_queue(self, message):
        async with self.progress_lock:
            self.game_progress_queue += message

    def set_scene(self, scene_description, winning_message=None, losing_message=None):
        """
        Set up the scene based on the provided description, handling both old and new formats.
        """
        if 'description' in scene_description:
            # New format with nested 'description', 'winning_message', etc.
            description_data = scene_description['description']
            self.winning_message = scene_description.get('winning_message', winning_message)
            self.losing_message = scene_description.get('losing_message', losing_message)
        else:
            # Legacy format where scene_description is directly the prompts
            description_data = scene_description
            self.winning_message = winning_message
            self.losing_message = losing_message

        # Extract prompts, states, and tools for each object
        self.scene_objects_prompts = {}
        self.scene_objects_states = {}
        self.scene_objects_tools = {}

        for key, value in description_data.items():
            if isinstance(value, dict) and 'description' in value:
                # New format: value is a dict with 'description', 'initial_state', 'tools'
                self.scene_objects_prompts[key] = value['description']
                self.scene_objects_states[key] = value.get('initial_state', {})
                self.scene_objects_tools[key] = value.get('tools', {})
            else:
                # Legacy format: value is just a description string
                self.scene_objects_prompts[key] = value
                self.scene_objects_states[key] = {}
                self.scene_objects_tools[key] = {}

    async def initialize_game_objects(self):    
        """
        Initialize game objects with their descriptions, states, and tools.
        """
        await self.add_to_progress_queue('<display_to_player> Filling room with objects...\n</display_to_player>')        

        # Updated game object template to include state and tools
        game_object_template = (
            'You simulate an object within a scene for a videogame. '
            'Keep track of your own description, state, and tools, using common sense to answer questions or change your state. '
            'Do not spontaneously add characteristics or tools without being provoked to do so. '
            'Do not disappear after being used. '
            'The object you simulate is a <object_name>. '
            'Your initial description is "<my_description>". '
            'Your initial state is <my_state>. '
            'Your available tools are <my_tools>. '
            'Important! Minimize changes when updating your state when possible. '
            'When queried, use your state as context. When updating, only use your tools or propose new ones. '
            'Only use your tools when clearly necessary.'
            'Be extremely brief'
        )

        # Initialize all game objects first
        for key in self.scene_objects_prompts.keys():
            self.game_objects[key] = GameObject(
                initial_state=copy.deepcopy(self.scene_objects_states[key]),
                initial_tools=copy.deepcopy(self.scene_objects_tools[key])
            )
            self.game_objects[key].object_name = key

        # Set system messages and initial states for all objects
        tasks = []
        for key in self.scene_objects_prompts.keys():
            applied_template = (
                game_object_template
                .replace('<object_name>', key)
                .replace('<my_description>', self.scene_objects_prompts[key])
                .replace('<my_state>', json.dumps(self.scene_objects_states[key]))
                .replace('<my_tools>', json.dumps({k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} for k, v in self.scene_objects_tools[key].items()}))
            )
            self.game_objects[key].set_system_message(applied_template)
            for tool_name, tool_data in self.scene_objects_tools[key].items():
                self.game_objects[key].tools[tool_name]['function'] = tool_data['function']
                    

            # No need for designer assistant; state is already set
            tasks.append(self.game_objects[key].process_game_input(
                f'This is your current state: "{json.dumps(self.scene_objects_states[key])}"'
            ))

        await asyncio.gather(*tasks)

    async def get_game_state(self):
        await self.add_to_progress_queue('<display_to_player>Computing game state...\n</display_to_player>')
        game_state = {k: json.dumps(v.state) for k, v in self.game_objects.items()}
        return game_state
        
        '''
        await self.add_to_progress_queue('<display_to_player>Computing game state...\n</display_to_player>')
        tasks = []
        summarization_prompt = 'What is your current state? Answer in first person: I...'
        
        for k, v in self.game_objects.items():
            tasks.append(v.process_game_input(summarization_prompt, keep_history=True))
        results = await asyncio.gather(*tasks)

        game_state = {k: result for k, result in zip(self.game_objects.keys(), results)}
        return game_state
        '''
    
    async def initialize_player_objects(self, player_id):
        """
        Initialize player_body_{player_id} and inventory_{player_id} for a new player.
        """
        # Define templates for player body and inventory
        player_body_template = (
            'You simulate an object within a scene for a videogame. '
            'Keep track of your own description, state, and tools, using common sense to answer questions or change your state. '
            'Do not spontaneously add characteristics or tools without being provoked to do so. '
            'Do not disappear after being used. '
            'The object you simulate is a <object_name>. '
            'Your initial description is "<my_description>". '
            'Your initial state is <my_state>. '
            'Your available tools are <my_tools>. '
            'Important! Minimize changes when updating your state when possible. '
            'When queried, use your state as context. When updating, only use your tools or propose new ones. '
            'Be extremely brief'
        )

        # Player body
        body_key = f"player_body_{player_id}"
        if body_key not in self.game_objects:
            self.game_objects[body_key] = GameObject(
                initial_state={"is_injured": False, "has_hands": True},
                initial_tools={}
            )
            self.game_objects[body_key].object_name = body_key
            body_prompt = (
                player_body_template
                .replace('<object_name>', body_key)
                .replace('<my_description>', "A player avatar, full of physical characteristics. A regular, able adventurer.")
                .replace('<my_state>', json.dumps({"is_injured": False, "has_hands": True}))
                .replace('<my_tools>', json.dumps({}))
            )
            self.game_objects[body_key].set_system_message(body_prompt)
            await self.game_objects[body_key].process_game_input(
                f'This is your current state: "{json.dumps({"is_injured": False, "has_hands": True})}"'
            )
            await self.add_to_progress_queue(f'<display_to_player> Player {player_id} body initialized.\n</display_to_player>')
            # Add to engine's active objects
            if self.engine_game_object:
                self.engine_game_object.add_active_game_object(body_key, self.game_objects[body_key])

        '''
        testing adding just player body
        # Inventory
        inventory_key = f"inventory_{player_id}"
        if inventory_key not in self.game_objects:
            self.game_objects[inventory_key] = GameObject(
                initial_state={"contents": []},
                initial_tools={
                    "add_item": {
                        "name": "add_item",
                        "description": "Adds an item to the inventory",
                        "function": lambda self, item: self.update_state({"contents": self.state["contents"] + [item]})
                    },
                    "remove_item": {
                        "name": "remove_item",
                        "description": "Removes an item from the inventory",
                        "function": lambda self, item: self.update_state({"contents": [i for i in self.state["contents"] if i != item]})
                    }
                }
            )
            self.game_objects[inventory_key].object_name = inventory_key
            inventory_prompt = (
                player_body_template
                .replace('<object_name>', inventory_key)
                .replace('<my_description>', "My set of possessions. It is initially empty.")
                .replace('<my_state>', json.dumps({"contents": []}))
                .replace('<my_tools>', json.dumps({"add_item": {"name": "add_item", "description": "Adds an item to the inventory"},
                                                  "remove_item": {"name": "remove_item", "description": "Removes an item from the inventory"}}))
            )
            self.game_objects[inventory_key].set_system_message(inventory_prompt)
            # Reattach lambda functions to tools
            self.game_objects[inventory_key].tools["add_item"]["function"] = lambda self, item: self.update_state({"contents": self.state["contents"] + [item]})
            self.game_objects[inventory_key].tools["remove_item"]["function"] = lambda self, item: self.update_state({"contents": [i for i in self.state["contents"] if i != item]})
            await self.game_objects[inventory_key].process_game_input(
                f'This is your current state: "{json.dumps({"contents": []})}"'
            )
            await self.add_to_progress_queue(f'<display_to_player> Player {player_id} inventory initialized.\n</display_to_player>')
            # Add to engine's active objects
            if self.engine_game_object:
                self.engine_game_object.add_active_game_object(inventory_key, self.game_objects[inventory_key])
        '''
        
    async def initialize_engine_simulator(self):
        await self.add_to_progress_queue('<display_to_player>Initializing game engine...\n</display_to_player>')
        game_engine_sys_prompt = (
            'You are a text game engine simulator. Your task is to reply using common sense to the questions about the player\'s text input to the game. '
            'I am the game designer. DO NOT add details or descriptions to any aspect of the game. '
            'Creating extra details is extraneous and detracts from the game experience. Be brief and concise in all your statements. '
            'You are called "game engine".'
        )
        game_state = await self.get_game_state()
        self.async_gameobject_init = []
        for key in self.game_objects.keys():
            self.async_gameobject_init.append(asyncio.create_task(
                self.game_objects[key].process_game_input(f'This is the state of all objects: "{str(game_state)}"')
            ))
        
        engine_initialization_prompt = ''
        if hasattr(self, 'scene_objects_responsibilities') and self.scene_objects_responsibilities:
            engine_initialization_prompt += f'This is every object in the room and their roles within the game: {str(self.scene_objects_responsibilities)}\n'
        engine_initialization_prompt += f'This is the current game state: {str(game_state)}'
        self.engine_game_object = EngineGameObject()
        self.engine_game_object.set_system_message(game_engine_sys_prompt)
        self.engine_game_object.winning_message = self.winning_message
        self.engine_game_object.losing_message = self.losing_message
        await self.engine_game_object.process_game_input(engine_initialization_prompt)
        for k, v in self.game_objects.items():
            self.engine_game_object.add_active_game_object(k, v)
        self.engine_game_object.game_state = game_state
        self.engine_game_object.object_name = 'game_engine'
        self.engine_game_object.roles_string = ''

    async def process_input(self, p_in):
        """Process commands from existing players"""
        if not p_in or not self.async_gameobject_init:
            return
        
        if self.async_gameobject_init != 'Done':
            await asyncio.gather(*self.async_gameobject_init)
            self.async_gameobject_init = 'Done'
            
        # Ensure new players are logged in first
        new_players = await self.login_new_players(p_in)            
        
        # Process commands for all players
        p_in_random = list(p_in.items())
        random.shuffle(p_in_random)
        player_input_dict = {}
        for new_player_id in new_players:
            command = f"A new player with id {new_player_id} has logged into the game. Their body and inventory have been added as gameobjects."
            prompt = f"{command}. Login priority number: -1\n"
            player_input_dict[new_player_id] = prompt   
        for random_index, (player_id, command) in enumerate(p_in_random):
            prompt = f"This is the input of the player with id {player_id}: {command}. Priority number:{random_index}\n"
            if player_id in player_input_dict.keys():
                player_input_dict[player_id] += prompt   
            else:
                player_input_dict[player_id] = prompt
        all_player_responses = await self.engine_game_object.process_player_input(player_input_dict) #currently, the game engine covers a zone. Will change when we have more zones in the game
        
        await self.print_game_state_and_tools()
        
        tools_dataset_file = "tools_dataset.json"
        try:
            async with aiofiles.open(tools_dataset_file, 'w') as f:
                await f.write(json.dumps(GameObject.tools_dataset, indent=4))
        except Exception as e:
            print(f"Error saving tools_dataset to JSON: {e}")
        
        for player_id, tailored_response in all_player_responses.items():
            yield player_id, tailored_response
            
    async def login_new_players(self, p_in):
        """Handle initialization and login of new players"""
        if not p_in:
            return
        
        # Check for new players and initialize their objects
        new_players = set(p_in.keys()) - self.active_players
        for player_id in new_players:
            if player_id.lower() == 'gamemaster':
                continue
            await self.initialize_player_objects(player_id)
            self.active_players.add(player_id)
            # Update engine game state after adding new player objects
            if self.engine_game_object:
                self.engine_game_object.game_state = await self.get_game_state()
        return new_players
    
    async def start_game(self):
        await self.initialize_game_objects()
        await self.initialize_engine_simulator()
        
    async def print_game_state_and_tools(self):
        """
        Print the current state dictionaries and tool datasets for all game objects,
        as well as the global tools dataset from GameObject.
        """
        await self.add_to_progress_queue('<display_to_player>Printing game state and tools...\n</display_to_player>')

        # Collect state and tools information
        output = "\n=== Game State and Tools ===\n"

        # Global tools dataset from GameObject class
        output += "Global Tools Dataset (GameObject.tools_dataset):\n"
        global_tools = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} 
                       for k, v in GameObject.tools_dataset.items()}
        output += json.dumps(global_tools, indent=2) + "\n\n"

        # Per-object state and tools
        for key, obj in self.game_objects.items():
            output += f"Object: {key}\n"
            
            # State dictionary
            output += "  State:\n"
            output += f"    {json.dumps(obj.state, indent=2)}\n"
            
            # Object-specific tools dataset (excluding function for readability)
            output += "  Tools:\n"
            tools_without_func = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} 
                                 for k, v in obj.tools.items()}
            output += f"    {json.dumps(tools_without_func, indent=2)}\n\n"

        # Add to progress queue and print to console
        await self.add_to_progress_queue(output)
        print(output)