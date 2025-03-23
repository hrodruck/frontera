async def handle_look(game, player_id, args, current_zone, current_subzone):
    """Handle !look command to describe the current location and visible objects."""
    if player_id not in game.player_locations:
        return "You haven’t joined the game yet!"

    print(f'{args=}')
    zone_data = game.zones.get("zones").get(current_zone)
    subzone_data = zone_data.get("subzones").get(current_subzone)

    
    if "more" in args.lower():
        zone_desc = zone_data.get("long_description", zone_data.get("short_description", "No zone description available"))
        subzone_desc = subzone_data.get("long_description", subzone_data.get("short_description", "No subzone description available"))

        objects_desc = ""
        if current_zone in game.game_objects and current_subzone in game.game_objects[current_zone]:
            objects = game.game_objects[current_zone][current_subzone]
            visible_objects = {
                obj.object_name: obj.state.get("human_readable_description", "No description available")
                for obj in objects.values()
                if not obj.state.get("is_hidden", False)
            }
            if visible_objects:
                objects_desc = "\nObjects here:\n" + "\n".join(
                    f"- {name}: {desc}" for name, desc in visible_objects.items()
                ) + "."

        return f"{zone_desc}\n{subzone_desc}{objects_desc}"

    zone_desc = zone_data.get("short_description")
    subzone_desc = subzone_data.get("short_description")

    objects_desc = ""
    if current_zone in game.game_objects and current_subzone in game.game_objects[current_zone]:
        objects = game.game_objects[current_zone][current_subzone]
        visible_objects = [obj.object_name for obj in objects.values() 
                         if not obj.state.get("is_hidden", False)]
        if visible_objects:
            objects_desc = "\nYou see: " + ", ".join(visible_objects) + "."

    return f"{zone_desc}\n{subzone_desc}{objects_desc}"