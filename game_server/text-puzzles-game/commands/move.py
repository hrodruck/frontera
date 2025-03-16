async def handle_move(game, player_id, args):
    """Handle !move command to change subzone."""
    subzone = args.strip().lower()
    if not subzone:
        return "Please specify a subzone to move to (e.g., !move prison-vault)"

    player_key = f"player_body_{player_id}"
    if player_key not in game.game_objects:
        return "You haven’t started exploring yet!"

    player = game.game_objects[player_key]
    current_zone = player.state.get("zone", "cinthria")
    current_subzone = player.state.get("subzone", "prison-vault")
    allowed_moves = player.state.get("allowed_moves", [])

    # Validate move
    zone_data = game.zones.get(current_zone, {})
    subzones = zone_data.get("subzones", {})
    if subzone not in subzones:
        return f"Subzone '{subzone}' doesn’t exist in {current_zone}!"
    if subzone == current_subzone:
        return f"You’re already in {subzone}!"
    if allowed_moves and subzone not in allowed_moves:
        return f"You can’t move to {subzone}!"

    # Update state
    player.update_state({"subzone": subzone})
    subzone_data = subzones.get(subzone, {})
    desc = subzone_data.get("short_description", "A mysterious place")
    return f"You move to {subzone}. {desc}"