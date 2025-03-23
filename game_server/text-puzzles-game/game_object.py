import json
import os
from copy import deepcopy
import asyncio
import inspect
import random
from backbone_comms import BackboneComms

class GameObject:
    # Global tools dataset shared across all GameObjects
    tools_dataset = {}

    @classmethod
    def load_tools_dataset(cls):
        """Load tools_dataset from JSON file and recreate lambda functions using eval."""
        tools_dataset_file = "data/tools_dataset.json"
        if os.path.exists(tools_dataset_file):
            try:
                with open(tools_dataset_file, 'r') as f:
                    loaded_tools = json.load(f)
                    # Reconstruct the tools_dataset with lambda functions using eval
                    for tool_name, tool_data in loaded_tools.items():
                        cls.tools_dataset[tool_name] = {
                            "name": tool_data["name"],
                            "human_readable_description": tool_data["human_readable_description"],
                            "function": tool_data["function"],
                            "reviewed": tool_data["reviewed"]
                        }
            except Exception as e:
                print(f"Error loading tools_dataset from {tools_dataset_file}: {e}")
                # Fallback to empty dataset if loading fails
                cls.tools_dataset = {}
        else:
            print(f"Tools dataset file {tools_dataset_file} not found. Initializing empty tools_dataset.")
            cls.tools_dataset = {}

    def __init__(self, initial_state=None, initial_tools=None):
        if not GameObject.tools_dataset:
            GameObject.load_tools_dataset()
        self.comms_backbone = BackboneComms()
        self.progress_queue = ''
        self._my_history = []
        self.progress_lock = asyncio.Lock()
        self.processing_lock = asyncio.Lock()
        self.comms_backbone.model_string = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

        self.object_name = ''
        # State dictionary to track object properties
        self.state = initial_state if initial_state is not None else {}
        # Tools dictionary specific to this object
        self.tools = initial_tools if initial_tools is not None else {}

    async def get_progress_queue(self):
        async with self.progress_lock:
            async for item in self.comms_backbone.read_comms_queue():
                self.progress_queue += f'{self.object_name}: {item}\n.\n'
                yield self.progress_queue
                self.progress_queue = ''
        await asyncio.sleep(0.02)

    async def chat_with_backbone(self, user_message, user_history=[], expect_json=False, keep_history=True, lock_history=True, expect_tools=False):
        return await self.comms_backbone.chat_outer(user_message, user_history, expect_json, keep_history, lock_history, expect_tools)

    async def add_to_progress_queue(self, message):
        async with self.progress_lock:
            self.progress_queue += message

    async def update_state(self, updates):
        if updates is None:
            return self.state
        """Helper method to safely update the state dictionary."""
        print (f'\n== called update_state==')
        print (f'{updates=}\n')
        async with self.processing_lock:
            try:
                self.state.update(updates)
            except Exception as e:
                print(e)
        return self.state
    
    
    async def get_reviewed_tools(self):
        approved_tools = {k:v for k, v in GameObject.tools_dataset.items() if v["reviewed"]==True}
        return json.dumps(approved_tools)

    async def process_game_input(self, input_contents, keep_history=True):
        """
        Process input from the game engine, distinguishing between query and update phases.
        """
        async with self.processing_lock:
            # Determine if this is a query or an update based on input structure
            current_state_str = json.dumps(self.state)
            if input_contents.startswith("Query:"):
                # Query phase: Provide information based on current state
                query = input_contents.replace("Query:", "").strip()
                prompt = (
                    f"Given my current state: {current_state_str}, answer this query: '{query}'. "
                    f"My role is {self.object_name}. Respond concisely in JSON: {{'response': 'answer'}}."
                    f"This is not the time to update anything, merely answer to the query and don't change your state yet."
                )
                reply = await self.chat_with_backbone(prompt, self._my_history, expect_json=True, keep_history=keep_history)
                reply = self.comms_backbone.load_json_from_llm(reply)['response']
            elif input_contents.startswith("Update:"):
                # Update phase: Modify state using tools
                update = input_contents.replace("Update:", "").strip()
                prompt = (
                    f"Given my current state: {current_state_str} and available tools: {json.dumps(self.tools)}, "
                    f"Now is the time to decide about updates to your state. "
                    f"How should I update myself based on this instruction: '{update}'? "
                    f"My role is {self.object_name}. "
                    f"If none of the available tools are adequate, propose a new tool. "
                    f"Return JSON: {{'action': 'use_tool'|'fetch_tool'|'propose_tool'|'no_action', 'tool_name': 'name', 'params': {{optional}}, 'new_tool': {{optional}}}}. "
                    f"If fetching a tool, you must choose one of the tools from the following: {await self.get_reviewed_tools()}"
                    f"Your order of preference should be to use_tool if possible, then fetch_tool if there's any match, then propose_tool or no_action if there is no particular modification to be made in the state."
                    f"To decide if fetch_tool is adequate, consider also the 'function' of that tool and interpret its behavior"
                    f"If proposing a tool, the 'new_tool' object must include: "
                    f"- 'name': the tool's name (string), "
                    f"- 'human_readable_description': what the tool does (string), "
                    f"- 'function': a lambda expression as a string (e.g., 'lambda self: self.update_state({{...}})') defining the tool’s behavior, "
                    f"- 'reviewed': a boolean (set to False), "
                    f"- 'params': an optional dictionary of parameters (e.g., {{'item': 'key'}}) if the lambda function requires arguments beyond 'self'. "
                    f"The lambda function should use 'self' to access and modify the object’s state via self.state or self.update_state(). "
                    f"Ensure the lambda function is valid Python syntax with no extra braces. Example: 'lambda self: self.update_state({{\"is_injured\": True}})'."
                    f"If the lambda function requires parameters beyond 'self', include them in the 'params' property of the 'new_tool' object for immediate execution. "
                    f"Example of a tool with parameters: "
                    f"'remove_item': {{'name': 'remove_item', 'human_readable_description': 'Removes a specific item from contents', 'function': 'lambda self, item: self.update_state({{\"contents\": [i for i in self.state[\"contents\"] if i != item]}}) if \"contents\" in self.state else None', 'reviewed': False, 'params': {{'item': 'key'}}}}. "
                    f"Example of a tool without parameters: "
                    f"'unlock': {{'name': 'unlock', 'human_readable_description': 'Unlocks the object if locked', 'function': 'lambda self: self.update_state({{\"is_locked\": False}}) if \"is_locked\" in self.state else None', 'reviewed': False}}. "
                    f"Ensure the proposed tool’s function and parameters (if any) are relevant to the instruction '{update}' and the current state."
                    f"Your order or preference should be use_tool, no_act, fetch_tool and, finally, propose_tool."
                )
                reply = await self.chat_with_backbone(prompt, self._my_history, expect_json=True, keep_history=keep_history)
                response_dict = self.comms_backbone.load_json_from_llm(reply)
                old_state = self.state.copy()
                update_message = await self.handle_update(response_dict, update)
                print (f"{self.object_name}'s tool update message:\n{update_message}\n")
            else:
                # Default to query if unclear
                query = input_contents.replace("Query:", "").strip()
                prompt = (
                    f"Given my current state: {current_state_str}, answer this query: '{query}'. "
                    f"My role is {self.object_name}. Respond concisely in JSON: {{'response': 'answer'}}."
                )
                reply = await self.chat_with_backbone(prompt, self._my_history, expect_json=True, keep_history=keep_history)
            return reply

    async def execute_tool(self, tool_func, tool_name, params):
        """Execute a tool function with dynamic parameter handling."""
        sig = inspect.signature(tool_func)
        param_count = len(sig.parameters)
        
        if param_count > 1:  # More than just 'self'
            if not params:
                return f"{self.object_name} failed to use tool '{tool_name}': parameters required but none provided. State: {json.dumps(self.state)}"
            extra_params = list(params.values())
            if len(extra_params) >= (param_count - 1):
                tool_func(self, *extra_params[:param_count - 1])
            else:
                return f"{self.object_name} failed to use tool '{tool_name}': insufficient parameters. State: {json.dumps(self.state)}"
        else:
            tool_func(self)
        return None  # Success case returns None, indicating the tool was executed

    async def handle_update(self, response_dict, update_instruction):
        """
        Apply tool-based updates and return the new state.
        Supports dynamic parameter detection and immediate execution of proposed tools.
        """
        action = response_dict.get("action")
        tool_name = response_dict.get("tool_name")
        params = response_dict.get("params", {})  # Optional parameters from LLM response
        
        if action == "use_tool" and tool_name in self.tools:
            tool_func = eval(self.tools[tool_name]["function"], {"self": self, "random":random})
            result = await self.execute_tool(tool_func, tool_name, params)
            if result:
                return result
            return f"{self.object_name} used tool '{tool_name}'. New state: {json.dumps(self.state)}"

        elif action == "fetch_tool" and tool_name in self.tools_dataset:
            if self.tools_dataset[tool_name]["reviewed"]:
                self.tools[tool_name] = self.tools_dataset[tool_name]
                tool_func = eval(self.tools[tool_name]["function"], {"self": self, "random":random})
                result = await self.execute_tool(tool_func, tool_name, params)
                if result:
                    return result
                return f"{self.object_name} fetched and used tool '{tool_name}'. New state: {json.dumps(self.state)}"
            else:
                return f"Tool '{tool_name}' is pending review and cannot be used yet."

        elif action == "propose_tool" and "new_tool" in response_dict:
            new_tool = response_dict["new_tool"]
            try:
                func_str = new_tool.get("function")
                if func_str and func_str.startswith("lambda"):
                    tool_func = eval(func_str, {"self": self, "random":random})
                else:
                    return f"{self.object_name} failed to propose tool '{new_tool['name']}': invalid function. State: {json.dumps(self.state)}"
                
                # Use params from new_tool if provided, otherwise empty dict
                tool_params = new_tool.get("params", {})
                result = await self.execute_tool(tool_func, new_tool['name'], tool_params)
                if result:
                    return result
                
                # Add to tools_dataset and tools as before
                new_tool["function"] = func_str
                new_tool.pop("params", None)
                new_tool["reviewed"] = False
                self.tools_dataset[new_tool["name"]] = new_tool
                local_tool = new_tool.copy()
                local_tool["reviewed"] = True
                self.tools[new_tool["name"]] = local_tool
                return f"{self.object_name} proposed and used new tool '{new_tool['name']}': {new_tool['human_readable_description']}. New state: {json.dumps(self.state)}"
            except Exception as e:
                return f"{self.object_name} failed to propose tool '{new_tool['name']}': {str(e)}. State: {json.dumps(self.state)}"
    
        elif action == "no_action":
            return f"{self.object_name} processed the update and concluded there was no action to be taken."
        else:
            return f"{self.object_name} could not process update '{update_instruction}'. No suitable tool found. State: {json.dumps(self.state)}"

    def set_system_message(self, message_contents):
        assert len(self._my_history) == 0
        self._my_history.append({'role': 'system', 'content': message_contents})

    def history_checkpoint(self):
        assert len(self._my_history) % 3 == 0
        self._checkpoint_len = len(self._my_history)

    def forget_old_history(self):
        assert len(self._my_history) % 3 == 0
        forgetting_len = min(self._checkpoint_len, len(self._my_history) - 3)
        self._my_history = deepcopy(self._my_history[forgetting_len:])
        assert len(self._my_history) % 3 == 0
        print(len(self._my_history))