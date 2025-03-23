import random

async def handle_spk(game, player_input_dict, zone, subzone):
    """Handle freeform !spk commands, passing them to the engine for processing."""
    if player_input_dict:
        total_commands = len(player_input_dict)
        if total_commands > 0:
            priority_numbers = random.sample(range(1, total_commands + 1), total_commands)
            for i, key in enumerate(player_input_dict.keys()):
                player_input_dict[key] = f"Priority: {priority_numbers[i]} - {player_input_dict[key]}"
    
    return await game.engine_game_objects[zone][subzone].process_player_input(player_input_dict)