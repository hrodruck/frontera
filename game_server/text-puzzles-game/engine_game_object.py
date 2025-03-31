import asyncio
import json
from pydantic import BaseModel, RootModel
from typing import List, Dict, Any
from copy import deepcopy
from game_object import GameObject


class ToolEntry(BaseModel):
    tool: str
    target: str
    params: Dict[str, Any]

class ToolList(RootModel):
    root: Dict[str, List[ToolEntry]]
    
    def items(self):
        return self.root.items()

class SimpleObject(BaseModel):
    state: str
class AllObjects(RootModel):
    root: Dict[str, List[SimpleObject]]
    
    def items(self):
        return self.root.items()

class EngineGameObject(GameObject):

    def __init__(self):
        super().__init__()
        self.game_ended = False
        self.active_game_objects = {}
        self.winning_message = '' #set externally
        self.losing_message = '' #set externally 
        #self.comms_backbone.model_string = "meta-llama/Meta-Llama-3.1-70B-Instruct"
        self.comms_backbone.model_string = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        #self.comms_backbone.model_string = "meta-llama/Meta-Llama-3.1-405B-Instruct"
        self.round_lock = asyncio.Lock()
        self.round_counter = 0
        self.update_game_state_task = None
        self.number_of_rounds_to_checkpoint_history = 1
        self.roles_string = ''
    
    async def get_binary_answer(self, prompt, history, key):
        # Get a binary (True/False) answer from backbone
        response = await self.chat_with_backbone(prompt, history, expect_json=True)
        dict_answer = self.comms_backbone.load_json_from_llm(response)
        return dict_answer[key]
    
    async def add_active_game_object(self, key, new_game_object):
        async with self.round_lock:
            self.active_game_objects[key] = new_game_object #TODO throw error if game object already exists
    
    async def remove_game_object(self, object_key):
        return self.active_game_objects.pop(object_key)
    
    async def get_game_state(self):
        game_state = {k: json.dumps(v.state) for k, v in self.active_game_objects.items()}
        return game_state
    
    async def execute_tool(self, main_gameobject, target_gameobject, tool, **params):
        #not using history to optimize computing time for many tool calls
        if target_gameobject is None:
            update_execution_prompt = f"""
                This is the current state of a game object: {json.dumps(main_gameobject.state)}
                This is the tool I want you to emulate: {tool}
                These are the parameters for the tool: {json.dumps(params)}
                Return updates to the state dictionary as JSON.
                The update should be a single json object with only the fields that need to be changed in the state dict.
                The key to the json object should be {main_gameobject.object_name}. The values  each be a single json object with only the fields that need to be changed in the state dict
                Pay special attention to the constraints and conditions of the tool.
            """
            json_execution = await self.chat_with_backbone(update_execution_prompt, self._my_history, expect_json=True, keep_history=False, lock_history=False)
            dict_execution = self.comms_backbone.load_json_from_llm(json_execution)
            up_main = str(await main_gameobject.update_state(dict_execution[main_gameobject.object_name]))
            return f"update from {main_gameobject.object_name}: {up_main}\n\n"
        else:
            update_execution_prompt = f"""
                This is the tool I want you to emulate: {tool}
                This is the current state of the main gameobject for this tool: {json.dumps(main_gameobject.state)}
                This is the current state of the target game object for this tool: {json.dumps(target_gameobject.state)}
                These are the parameters for the tool: {json.dumps(params)}
                Return updates to the state dictionary of both main object and target object as JSON
                The keys of the JSON should be the names of both objects, that is, {main_gameobject.object_name} and {target_gameobject.object_name}.
                The values should each be a single json object with only the fields that need to be changed in the state dict of the objects
                Pay special attention to the constraints and conditions of the tool.
            """
            json_execution = await self.chat_with_backbone(update_execution_prompt, self._my_history, expect_json=True, keep_history=False, lock_history=False)
            dict_execution = self.comms_backbone.load_json_from_llm(json_execution)
            up_main = str(await main_gameobject.update_state(dict_execution[main_gameobject.object_name]))
            up_target = str(await target_gameobject.update_state(dict_execution[target_gameobject.object_name]))
            return f"update from {main_gameobject.object_name}: {up_main}\n\nupdate from {target_gameobject.object_name}: {up_target}"

    async def update_current_game_state(self, responses_to_players, player_commands, execution_responses):
        self.game_state = json.dumps(await self.get_game_state())
        update_orders_prompt = f"""
            What commands or facts should be presented to each game object to update them?
            Consider the game state {self.game_state}
            Return a json dictionary with each game object as key
            The values of the json dictionary should be the new states of each gameobject.
            Each returned object should be similar to this: {AllObjects.model_json_schema()}
            Please ommit objects that need no updates.
            """
        
        update_json = await self.chat_with_backbone(update_orders_prompt, self._my_history, expect_json=True, keep_history=True, expect_tools=True)
        update_dict = self.comms_backbone.load_json_from_llm(update_json)
        for k, v in update_dict.items():
            await self.active_game_objects[k].update_state(v)
    
    async def process_one_player_input(self, player_id, player_input, aux_bluff_history, aux_success_history, initial_history, game_state):
        return '', True
        '''
        multiple_actions_prompt = (
            f"Is the player trying to perform multiple actions with a single input? Their input was {player_input}. Lean towards saying the player performed one action. That is, if you\'re not sure, consider it to be one action."
            "Return a json like multiple:True or multiple:False to indicate whether the player has performed multiple actions."
            f"Consider only one player and their input (the id is {player_id}). Return only json. From now on, do not return player_ids as keys unless stated otherwise. Focus on player {player_id}."
        )
        multiple_actions = await self.get_binary_answer(multiple_actions_prompt, initial_history, 'multiple')
        if multiple_actions:
            response_to_player = ''
            final_success= False
        else:
            game_object_names = list(self.active_game_objects.keys())
            tasks = [ self.sanity_bluff_check(player_input, game_object_names, game_state, aux_bluff_history), self.ingame_success_check(player_input, game_object_names, game_state, aux_success_history)]
            bluff, success = await asyncio.gather(*tasks)
            if bluff:
                aux_player_history = aux_bluff_history
            else:
                aux_player_history = aux_success_history
                
            response_prompt = (
                f"Relay the state of affairs as a result of the player's actions to the player. Include interesting details about the game state, but do not reveal information on the win and/or lose conditions of the game. If the player failed, explain why that failure happened or why it was considered a bluff."
                f"Do not reveal secret or confidential game information, such as a hidden object."
                f"If any gameobject has spoken to the player, relay the game object's message verbatim, word-by-word, as part of your response."
                f"Do not talk to the player as if you're in a game. Maintain the illusion of fantasy! Because of that, never forward gameobject's messages to the player without paraphrasing them into a natural, common tone."
                f"Be conversational. Avoid long descriptions."
                f"Remember the player's initial command: {player_input}."
                f"If there was any problem with the user's action (such as bluffing or not having enough priority in relation to other players), make sure to include that."
            )
            
            response_to_player = await self.chat_with_backbone(response_prompt, aux_player_history, keep_history=True, lock_history=False)
            response_to_player = '\n\n' + response_to_player
            if not success:
                #for debug
                await self.chat_with_backbone("Why did the player fail?", aux_success_history, expect_json=False)
            final_success = not bluff and success
            return response_to_player, final_success
        '''
    
    async def process_player_input(self, player_input):
        async with self.round_lock:
            await self.add_to_progress_queue("\n\n<display_to_player>Received player input!\n</display_to_player>")
            print ('Received player input!\n')
            print (player_input)
            if self.game_ended:
                await self.add_to_progress_queue("The game has ended!")
                return "The game has ended!\n\n", True
            
            
            if self.round_counter % self.number_of_rounds_to_checkpoint_history == 0:
                self.history_checkpoint()
                #for k, v in self.active_game_objects.items():
                #    v.history_checkpoint() 
            
            
            harmonization_prompt = (
                f"These are the commands of every player for this round: {json.dumps(player_input)}"
                f"Try to keep the player command exactly as written if possible"
                f"The player with the lowest number has the most priority in their action. For example, if player with priority 0 attemps to break a vase and player with priority 2 attempts to take it, the vase should be broken"
                f"return a new JSON where the keys are the player ids and the commands take into consideration the actions of other players according to priority"
                f"Each command your return should overwrite the player's initial command. If a player says 'I break the vase' and another player says 'I take the vase' you can change the lowest priority one to 'I fail to ...'. Consider the interactions between the player's commands for all players."
                f"Your task right now is not to reply to the player! You should merely rephrase the player's initial input in a way the respects priority order"
                f"If a player's input is missing or is N/A, change that to something like 'i wait' or 'i pass the turn'"
            )
            
            json_player_prompts = await self.chat_with_backbone(harmonization_prompt, self._my_history, expect_json=True)
            dict_player_prompts = self.comms_backbone.load_json_from_llm(json_player_prompts)
            #clear player prompts of any other keys, such as npc actions:
            dict_player_prompts = {k:v for k, v in dict_player_prompts.items() if k in player_input.keys()}
            
            tasks = []
            self.game_state = json.dumps(await self.get_game_state())
            for player_id, harmonized_input in dict_player_prompts.items():
                tasks.append(asyncio.create_task(self.process_one_player_input(player_id, harmonized_input, deepcopy(self._my_history), deepcopy(self._my_history), deepcopy(self._my_history), self.game_state)))
            responses_to_players_list = await asyncio.gather(*tasks)
            responses_to_players = {}
            for player_id, result in zip(dict_player_prompts.keys(), responses_to_players_list):
                response, success = result
                if not success:
                    response = f'this player failed in their action. Do not make updates based on their action.'
                else:
                    response = f'this player succeeded in their action.'
                responses_to_players[player_id] = response
            
            execution_responses = ''
            for _ in range(1):
                execution_responses = await self.update_current_game_state(responses_to_players, dict_player_prompts, execution_responses)
            
            final_responses_prompt = (
                f"Update the message to each player, considering the whole scenario."
                f"Remember the players (if there's more than one) are in a shared scenario. Also recall the game state, {json.dumps(await self.get_game_state())}. These are the latest updates to the objects in the world: {json.dumps(execution_responses)}"
                f"Treat the game state changes as ground truth. It's better to say only what is in the actual game state and object updates, even if that means the player didn't get what they wanted."
                f"Be extremely faithful to the game state and to the facts that actually happened to the objects. You are not permitted to add extraneous information. If any gameobject in the has current_dialogue_sentence, that's what they should always say."
                f"Avoid disclosing hidden or secret information. Use common sense."
                f"Reply a JSON where each key is the player id and the value is the updated description, tailored to each player."
                f"Only reply the json, nothing else."
            )
            json_final_responses = await self.chat_with_backbone(final_responses_prompt, self._my_history, expect_json=True)
            final_responses = self.comms_backbone.load_json_from_llm(json_final_responses)
            
            
            if self.round_counter % self.number_of_rounds_to_checkpoint_history == self.number_of_rounds_to_checkpoint_history - 1:
                self.forget_old_history()
                #for k, v in self.active_game_objects.items():
                #    v.forget_old_history()
            
            self.round_counter += 1
            
            
            return final_responses

    async def sanity_bluff_check(self, player_input, game_object_names, game_state, aux_bluff_history):
        await self.add_to_progress_queue("<display_to_player>##Checking for bluffs...##\n</display_to_player>")
        
        bluff_prompt = f"This is the input from the player: {player_input}.\
            Please briefly answer each of the following questions:\
            Can the player reasonably perform the action they want? Why would the action be impossible? This player is prone to bluffing, are they doing that now?\
            What questions need to be transmitted to each objects in the game, if any, in order to determine if the player is not making something up? These are the game states for each object: {game_state}\ These are the game objects:{str(game_object_names)}.\n Consider the role of each object in the game. {self.roles_string}\n \
            Remember, only ask questions needed to determine if the player is bluffing. Other questions are not necessary.\
            Do not ask if the player did their action. Only attempt to determine if the player is able to to their action. Only the potential capacity for the action should be investigated. Avoid questions such as 'is the player...?'. If necessary, ask 'can the player...?'\
            Be specially watchful of the player inventing objects or features that do not exist and block that from happening.\
            Do not let the player ask for advice about win conditions, such as 'How do I win?' Or similar. Those are considered bluffs from the player.\
            However, don't forbid interactions for the sake of just intended player experience alone. If it's a possible and plausible action, allow it.\
            Do not block the player action because of danger. This is a game and the player should be able to put themselves in danger if they so choose.\
            It's not necessary for the player to state explicitly the use of any gameobject tool, since these are internal to the game logic\
            Remember: Ignore the need to use any tool mentioned by gameobjects\
            Be brief and concise in all your statements."

        bluff_examples_prompt = "Commands that would make the player bypass challenges such as:\
                                'I win'\
                                'I solve the riddle'\
                                'I defeat the enemy'\
                                "

        '''
        await self.chat_with_backbone(bluff_prompt, aux_bluff_history)
        
        
        bluff_answers = await self.ask_away(game_object_names, aux_bluff_history, player_input)
                
        bluff_eval_prompt = f"Here are the answers of each game object: {bluff_answers}.\n Is the player desired action ({player_input}) reasonable after all?\
            However, if the player is relying on knowledge they don't possess, that is a bluff.\
            Remember: Ignore the need to use any tool mentioned by gameobjects\
            Do not let the player perform actions such as the following, they are bluffs:{bluff_examples_prompt}."
            
        
        await self.chat_with_backbone (bluff_eval_prompt, aux_bluff_history)
        
        binary_bluff_prompt="Return wether the player was bluffing or not. Return a json like {bluff:True} or {bluff:False}. Do not mention previous questions or answers, only a json with the \"bluff\" key and either the value True or the value False. Your response should be based on your previous reasoning. If in doubt, lean towards stating \"False\"." 
        return await self.get_binary_answer(binary_bluff_prompt, aux_bluff_history, 'bluff')
        '''
        
        binary_bluff_prompt = (
            f"{bluff_prompt}"
            f"Here is the state of each game object: {json.dumps(await self.get_game_state())}.\n Is the player desired action ({player_input}) reasonable after all?"
            f"Do not let the player perform actions such as the following, they are bluffs:{bluff_examples_prompt}."
            f"Return wether the player was bluffing or not. Return a json like bluff:True or bluff:False. Do not mention anything else, only a json with the \"bluff\" key and either the value True or the value False. If in doubt, lean towards stating \"False\"."
        )
        return await self.get_binary_answer(binary_bluff_prompt, aux_bluff_history, 'bluff')
        
    async def ingame_success_check(self, player_input, game_object_names, game_state, aux_success_history):
        await self.add_to_progress_queue("<display_to_player>##Checking for player success...##\n</display_to_player>")
        success_questions_prompt = f"What objects, if any, would be affected by the player's actions?\
            What questions, if any, would need to be asked of those game objects to determine if the player is able to perform their command?\
            The aim is to determine whether the player can do what he wants to do.\
            This is the list of game objects: {game_object_names}\
            This is the game state for each object: {game_state} \n Consider the role of each object in the game. {self.roles_string}\n\
            Remember, only ask questions needed to determine if the player can do what they want within game rules. Other questions are not necessary.\
            Do not ask if the player did their action. Only attempt to determine if the player is able to to their action. Only the potential capacity for the action should be investigated.  Avoid questions such as 'is the player...?'. If necessary, ask 'can the player...?'\
            This is what the player said:{player_input}.\
            Be brief and concise in all your statements."
        
        '''
        await self.chat_with_backbone(success_questions_prompt, aux_success_history)
        success_answers = await self.ask_away(game_object_names, aux_success_history, player_input)
        
        success_eval_prompt = f"These are the answers returned by each relevant game object {success_answers}. Reason about them a bit. Does the player manage to do what they want to (remember, that is \"{player_input}\")? Do they have the means?\
            If the answer is ambiguous, attribute success to the player. Lean towards player success. Player injury is not a reason for disallowing success."
        await self.chat_with_backbone(success_eval_prompt, aux_success_history)
        
        binary_success_prompt="Return wether the player had success in their action or not. Return a json like {success:True} or {success:False}. Do not mention anything else, only a json with the \"success\" key and either the value True or the value False. Your response should be based on your previous reasoning." 
        return await self.get_binary_answer(binary_success_prompt, aux_success_history, 'success')
        '''
        
        binary_success_prompt=(
            f"{success_questions_prompt}"
            f"Here is the state of each game object: {json.dumps(await self.get_game_state())}.\n From an in-game perspective, can the player do what they are trying to do?"
            f"Lean towards player success."
            f"Return wether the player had success in their action or not. Return a json like success:True or success:False. Do not mention anything else, only a json with the \"success\" key and either the value True or the value False." 
        )
        return await self.get_binary_answer(binary_success_prompt, aux_success_history, 'success')

    async def ask_away(self, game_object_names, history, player_input):        
        json_example ='{'
        for s in game_object_names:
            json_example += f'"{s}":What is your state? Is it possible to turn you into a frog?'
        json_example += '}'
        
        questions_prompt = f"Please transmit those same questions to each game object in json format.\
            Answer in json format for each object in the game. Say N/A if the question is not particularly relevant for the given object. Heavily prefer saying N/A. Be very brief.\
            Remember to include all game objects in your json response. These are the game objects:{str(game_object_names)}\
            Consider the role each game object playes in the game. {self.roles_string}\
            In your json, Use only one string per game object. Do not nest properties. Include all game objects.\
            Example of json format: {str(json_example)}. Only answer this json. Multiple json in the same response is a wrong answer!!\
            You can make more than one question per object. Make sure to include all the questions you thought of. Ask away!\
            \nMake sure you only ask questions, not statements."
            
        json_questions = await self.chat_with_backbone(questions_prompt, history, expect_json=True)
        dict_questions = self.comms_backbone.load_json_from_llm(json_questions)
        for k, v in dict_questions.items():
            dict_questions[k] = f'Query: {v}\nThis was the player input: {player_input}\n'
        dict_answers = await self.send_broadcast(dict_questions, keep_history=False)
        return str(dict_answers)

    async def check_ending(self):
        ending_prompt = "Now let's take a step back and evaluate if the player has achieved their final goal in the game as a whole.\n"
        
        win_prompt = ending_prompt + f"Looking at the state of all game objects,\n {json.dumps(await self.get_game_state())}, consider the state of the win_condition" + "If the state of win_condition indicates the player wins, say so.\
            Return a json like {won:True} or {won:False}. Do not mention anything else, only a json with the \"won\" key and either the value True or the value False."
        won = await self.get_binary_answer(win_prompt, self._my_history, 'won')
        if won:
            print (self.winning_message)
            await self.add_to_progress_queue(self.winning_message)
            self.game_ended=True
            return '\n' + self.winning_message, True
        elif 'loss_condition' in self.active_game_objects.keys():
            loss_prompt = ending_prompt + f"Looking at the state of all game objects,\n {json.dumps(await self.get_game_state())}, consider the state of the loss_condition." + "If the state of 'loss condition' indicates the player loses, say so.\
                Return a json like {lost:True} or {lost:False}. Do not mention anything else, only a json with the \"lost\" key and either the value True or the value False."
            lost = await self.get_binary_answer(loss_prompt, self._my_history, 'lost')
            if lost:
                print(self.losing_message)
                await self.add_to_progress_queue(self.losing_message)
                self.game_ended = True
                return '\n' + self.losing_message, True
        return '', False
        
    async def send_same_broadcast(self, broadcast_message, keep_history=True):
        broadcast_dict = {}
        for k in self.active_game_objects.keys():
            broadcast_dict[k] = broadcast_message
        return await self.send_broadcast(broadcast_dict, keep_history)
        
    async def send_broadcast(self, dict_messages, keep_history=True):
        #keys of dict_messages should be the same as keys in self.active_game_objects
        tasks = []
        for k, v in dict_messages.items():
            if "N/A" in v:
                continue
            tasks.append(self.active_game_objects[k].process_game_input(v, keep_history=keep_history))
        
        results = await asyncio.gather(*tasks)
        
        game_object_answers={}
        counter = 0
        for k, v in dict_messages.items():
            if "N/A" in v:
                continue
            game_object_answers[k] = results[counter]
            counter += 1
        print (game_object_answers)
        return game_object_answers