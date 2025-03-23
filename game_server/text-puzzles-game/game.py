import asyncio
import copy
import json
import random
from engine_game_object import EngineGameObject
from game_object import GameObject
from commands.spk import handle_spk
from commands.move import handle_move
from commands.look import handle_look
from commands.not_found import handle_command_not_found

class Game:
    def __init__(self):
        self.game_ended = False
        self.game_progress_queue = ''
        self.progress_lock = asyncio.Lock()
        self.game_objects = {}  # zone -> subzone -> object_name -> GameObject
        self.engine_game_objects = {}  # zone -> subzone -> EngineGameObject
        self.active_players = set()
        self.zones = {}  # All zones data
        self.scene_objects_states = {} # Initial state loaded from data for every object
        self.scene_objects_tools = {} # Initial tools loaded from data for every object
        self.player_locations = {}  # player_id -> {"zone": str, "subzone": str}
        print("Engine is running. Use set_all_zones and start_game!")

    async def set_all_zones(self, zones):
        """Store all zones data."""
        self.zones = zones
        for zone in self.zones["zones"]:
            for subzone in self.zones["zones"][zone]["subzones"]:
                if zone not in self.game_objects:
                    self.game_objects[zone] = {}
                    self.engine_game_objects[zone] = {}
                    self.scene_objects_states[zone]={}
                    self.scene_objects_tools[zone]={}
                if subzone not in self.game_objects[zone]:
                    self.game_objects[zone][subzone] = {}
                    self.engine_game_objects[zone][subzone] = {}
                    self.scene_objects_states[zone][subzone]={}
                    self.scene_objects_tools[zone][subzone]={}
                    
                subzone_data = self.zones["zones"][zone]["subzones"][subzone]
                print (f'loading subzone data for subzone {subzone} in zone {zone}')
                scene_description = subzone_data.get("objects", {})
                if scene_description:
                    await self.set_scene_one_subzone(
                        scene_description=scene_description,
                        zone=zone,
                        subzone=subzone,
                    )
                else:
                    print (f'could not find objects in subzone {subzone}!')

    async def set_scene_one_subzone(self, scene_description, zone, subzone):
        for key, value in scene_description.items():
            self.scene_objects_states[zone][subzone][key] = value.get('initial_state')
            self.scene_objects_tools[zone][subzone][key] = value.get('tools')

    async def initialize_game_objects(self, zone, subzone):
        """Initialize game objects for a specific zone and subzone."""
        await self.add_to_progress_queue(f'<display_to_player> Filling {zone}/{subzone} with objects...\n</display_to_player>')
        print(f'Filling {zone}/{subzone} with objects...')
        game_object_template = (
            'You simulate an object within a scene for a videogame. '
            'Keep track of your own description, state, and tools, using common sense to answer questions or change your state. '
            'Do not spontaneously add characteristics or tools without being provoked to do so. '
            'Do not disappear after being used. '
            'The object you simulate is a <object_name>. '
            'Your initial state is <my_state>. '
            'Your available tools are <my_tools>. '
            'Important! Minimize changes when updating your state when possible. '
            'When queried, use your state as context. When updating, only use your tools or propose new ones. '
            'Only use your tools when clearly necessary.'
            'Be extremely brief'
        )
        for key in self.scene_objects_states[zone][subzone].keys():
            self.game_objects[zone][subzone][key] = GameObject(
                initial_state=copy.deepcopy(self.scene_objects_states[zone][subzone][key]),
                initial_tools=copy.deepcopy(self.scene_objects_tools[zone][subzone][key])
            )
            self.game_objects[zone][subzone][key].object_name = key
            applied_template = (
                game_object_template
                .replace('<object_name>', key)
                .replace('<my_state>', json.dumps(self.scene_objects_states[zone][subzone][key]))
                .replace('<my_tools>', json.dumps({k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} for k, v in self.scene_objects_tools[zone][subzone][key].items()}))
            )
            self.game_objects[zone][subzone][key].set_system_message(applied_template)
            
            '''
            await self.game_objects[zone][subzone][key].process_game_input(
                f'This is your current state: "{json.dumps(self.scene_objects_states[zone][subzone][key])}"'
            )
            '''
            

    async def initialize_engine_simulator(self, zone, subzone):
        """Initialize the engine for a specific zone and subzone."""
        await self.add_to_progress_queue(f'<display_to_player>Initializing game engine for {zone}/{subzone}...\n</display_to_player>')
        print(f'Initializing game engine for {zone}/{subzone}...')
        game_engine_sys_prompt = (
            'You are a text game engine simulator. Your task is to reply using common sense to the questions about the player\'s text input to the game. '
            'I am the game designer. DO NOT add details or descriptions to any aspect of the game. '
            'Creating extra details is extraneous and detracts from the game experience. Be brief and concise in all your statements. '
            'You are called "game engine".'
        )
        game_state = await self.get_game_state(zone, subzone)
        self.engine_game_objects[zone][subzone] = EngineGameObject()
        self.engine_game_objects[zone][subzone].set_system_message(game_engine_sys_prompt)
        await self.engine_game_objects[zone][subzone].process_game_input(f'This is the current state of the objects within you: {json.dumps(game_state)}')
        for k, v in self.game_objects[zone][subzone].items():
            await self.engine_game_objects[zone][subzone].add_active_game_object(k, v)
        self.engine_game_objects[zone][subzone].game_state = game_state

    async def start_game(self, zone, subzone):
        """Start the game"""
        for zone, v in self.engine_game_objects.items():
            for subzone, engineobject in v.items():
                await self.initialize_game_objects(zone, subzone)
                await self.initialize_engine_simulator(zone, subzone)

    async def process_player_commands(self, p_in):
        if not p_in:
            return 
        tasks = []  # List for non-!spk tasks
        spk_groups = {}  # Dictionary to group !spk inputs by (zone, subzone)

        # Step 1: Categorize commands and ensure zones are initialized
        for player_id, command in p_in.items():
            zone = self.player_locations[player_id]["zone"]
            subzone = self.player_locations[player_id]["subzone"]

            prefix, args = self.parse_command(command)
            if prefix == "!spk":
                # Group !spk inputs by (zone, subzone)
                key = (zone, subzone)
                if key not in spk_groups:
                    spk_groups[key] = {}
                spk_groups[key][player_id] = args  # Store args directly
            else:
                # Handle non-!spk commands (e.g., !move, !look) as parallel tasks
                handler_map = {
                    "!move": handle_move,
                    "!look": handle_look
                }
                handler = handler_map.get(prefix, handle_command_not_found)
                if handler:
                    task = asyncio.create_task(handler(self, player_id, args, zone, subzone))
                    tasks.append((player_id, task))

        # Step 2: Process !spk commands in parallel for each zone/subzone
        spk_tasks = []
        for (zone, subzone), player_input_dict in spk_groups.items():
            task = asyncio.create_task(handle_spk(self, player_input_dict, zone, subzone))
            spk_tasks.append(((zone, subzone), task))

        if spk_tasks:
            spk_results = await asyncio.gather(*(task for _, task in spk_tasks))
            # Yield results from each !spk task
            for (_, _), result_dict in zip(spk_tasks, spk_results):
                for player_id, response in result_dict.items():
                    zone = self.player_locations[player_id]["zone"]
                    subzone = self.player_locations[player_id]["subzone"]
                    body_key = f"player_body_{player_id}"
                    new_zone = self.game_objects[zone][subzone][body_key].state["zone"]
                    if new_zone != zone:
                        await handle_move(self, player_id, new_zone, zone, subzone)
                    new_subzone = self.game_objects[zone][subzone][body_key].state["subzone"]
                    if new_subzone != subzone:
                        await handle_move(self, player_id, new_subzone, zone, subzone)
                    yield player_id, response

        # Step 3: Process non-!spk commands in parallel
        if tasks:
            results = await asyncio.gather(*(task for _, task in tasks))
            for (player_id, _), response in zip(tasks, results):
                yield player_id, response
        await self.print_game_state_and_tools()
    
    async def get_game_state(self, zone, subzone):
        """Get the game state for a specific zone and subzone."""
        await self.add_to_progress_queue(f'<display_to_player>Computing game state for {zone}/{subzone}...\n</display_to_player>')
        print(f'Computing game state for {zone}/{subzone}...')
        game_state = {k: json.dumps(v.state) for k, v in self.game_objects[zone][subzone].items()}
        print (game_state)
        return game_state

    async def get_progress_queue(self):
        '''Deprecated until we figure out how to do this per subzone'''
        raise StopAsyncIteration
        """Yield progress updates."""
        if not self.game_ended:
            async with self.progress_lock:
                if self.game_progress_queue:
                    yield self.game_progress_queue
                    self.game_progress_queue = ''
                for zone in self.engine_game_objects:
                    for subzone in self.engine_game_objects[zone]:
                        async for item in self.engine_game_objects[zone][subzone].get_progress_queue():
                            yield item
                        for obj in self.game_objects[zone][subzone].values():
                            async for item in obj.get_progress_queue():
                                yield item
            await asyncio.sleep(0.02)
        else:
            raise StopAsyncIteration

    async def add_to_progress_queue(self, message):
        """Add a message to the progress queue."""
        async with self.progress_lock:
            self.game_progress_queue += message

    def parse_command(self, command):
        """Parse command into prefix and arguments."""
        parts = command.strip().split(" ", 1)
        prefix = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        return prefix, args

    async def add_player(self, player_id, zone, subzone):
        """Add a player to the game with an initial location."""
        if player_id not in self.player_locations:
            self.player_locations[player_id] = {"zone": zone, "subzone": subzone}
            self.active_players.add(player_id)
            await self.add_to_progress_queue(f'<display_to_player>Player {player_id} joined at {zone}/{subzone}.\n</display_to_player>')
            print(f'Player {player_id} joined at {zone}/{subzone}.')
            await self.initialize_player_objects(player_id)
    
    async def initialize_player_objects(self, player_id):
        """Initialize player_body_{player_id} for a new player in their current zone/subzone."""
        if player_id not in self.player_locations:
            raise ValueError(f"Player {player_id} must be added to player_locations before initializing objects.")

        # Get the player's current location
        zone = self.player_locations[player_id]["zone"]
        subzone = self.player_locations[player_id]["subzone"]

        # Load template from JSON file or use fallback
        with open('data/player_template.json', 'r') as f:
                template_data = json.load(f)

        # Define base prompt template
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

        # Player body key
        body_key = f"player_body_{player_id}"

        # Ensure the zone/subzone exists in game_objects
        if zone not in self.game_objects:
            self.game_objects[zone] = {}
        if subzone not in self.game_objects[zone]:
            self.game_objects[zone][subzone] = {}

        # Initialize the player body object if it doesn’t exist
        if body_key not in self.game_objects[zone][subzone]:
            self.game_objects[zone][subzone][body_key] = GameObject(
                initial_state=template_data["initial_state"],
                initial_tools=template_data["initial_tools"]
            )
            self.game_objects[zone][subzone][body_key].object_name = body_key
            body_prompt = (
                player_body_template
                .replace('<object_name>', body_key)
                .replace('<my_description>', template_data["human_readable_description"])
                .replace('<my_state>', json.dumps(template_data["initial_state"]))
                .replace('<my_tools>', json.dumps(template_data["initial_tools"]))
            )
            self.game_objects[zone][subzone][body_key].set_system_message(body_prompt)
            '''
            await self.game_objects[zone][subzone][body_key].process_game_input(
                f'This is your current state: "{json.dumps(template_data["initial_state"])}"'
            )
            '''
            await self.add_to_progress_queue(f'<display_to_player> Player {player_id} body initialized in {zone}/{subzone}.\n</display_to_player>')
            print(f'Player {player_id} body initialized in {zone}/{subzone}.')

            # Add to the zone/subzone engine’s active objects
            if zone in self.engine_game_objects and subzone in self.engine_game_objects[zone]:
                await self.engine_game_objects[zone][subzone].add_active_game_object(
                    body_key, self.game_objects[zone][subzone][body_key]
                )

    async def print_game_state_and_tools(self):
        """Print the current state dictionaries and tool datasets for all game objects."""
        await self.add_to_progress_queue('<display_to_player>Printing game state and tools...\n</display_to_player>')
        print('Printing game state and tools...')

        output = "\n=== Game State and Tools ===\n"
        output += "Global Tools Dataset (GameObject.tools_dataset):\n"
        global_tools = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} 
                       for k, v in GameObject.tools_dataset.items()}
        output += json.dumps(global_tools, indent=2) + "\n\n"

        for zone in self.game_objects:
            for subzone in self.game_objects[zone]:
                for key, obj in self.game_objects[zone][subzone].items():
                    output += f"Object: {key} (in {zone}/{subzone})\n"
                    output += "  State:\n"
                    output += f"    {json.dumps(obj.state, indent=2)}\n"
                    output += "  Tools:\n"
                    tools_without_func = {k: {k2: v2 for k2, v2 in v.items() if k2 != 'function'} 
                                         for k, v in obj.tools.items()}
                    output += f"    {json.dumps(tools_without_func, indent=2)}\n\n"

        await self.add_to_progress_queue(output)
        print(output)