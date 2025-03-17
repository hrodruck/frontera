async def handle_look(game, player_id, args, current_zone, current_subzone):
    """Handle !look command to describe the current location and visible objects."""
    if player_id not in game.player_locations:
        return "You haven’t joined the game yet!"

    # Use current_zone and current_subzone passed from process_input
    zone_data = game.zones.get("zones").get(current_zone)
    zone_desc = zone_data.get("description")
    subzone_data = zone_data.get("subzones").get(current_subzone)
    subzone_desc = subzone_data.get("long_description", subzone_data.get("short_description"))

    # List visible objects in the current subzone
    objects_desc = ""
    if current_zone in game.game_objects and current_subzone in game.game_objects[current_zone]:
        objects = game.game_objects[current_zone][current_subzone]
        visible_objects = [obj.object_name for obj in objects.values() 
                          if not obj.state.get("is_hidden", False)]
        if visible_objects:
            objects_desc = "\nYou see: " + ", ".join(visible_objects) + "."

    return f"{zone_desc}\n{subzone_desc}{objects_desc}"