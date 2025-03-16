async def handle_look(game, player_id, args):
    """Handle !look command to describe the current location."""
    player_key = f"player_body_{player_id}"
    if player_key not in game.game_objects:
        return "You haven’t started exploring yet!"

    player = game.game_objects[player_key]
    current_zone = player.state.get("zone", "cinthria")
    current_subzone = player.state.get("subzone", "prison-vault")

    zone_data = game.zones.get(current_zone, {})
    zone_desc = zone_data.get("description", "An unknown land")
    subzone_data = zone_data.get("subzones", {}).get(current_subzone, {})
    subzone_desc = subzone_data.get("long_description", subzone_data.get("short_description", "A strange place"))

    return f"{zone_desc}\n{subzone_desc}"