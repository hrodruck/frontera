async def handle_spk(game, player_input_dict, zone, subzone):
    """Handle freeform !spk commands, passing them to the engine for processing."""
    return await game.engine_game_objects[zone][subzone].process_player_input(player_input_dict)