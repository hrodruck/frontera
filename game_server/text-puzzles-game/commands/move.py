async def handle_move(game, player_id, args, current_zone, current_subzone):
    """Handle movement between zones and subzones."""
    target = args.strip()
    target = target.replace('_', '-')
    if not target:
        return "Where do you want to move?"

    if player_id not in game.player_locations:
        return "You haven’t joined the game yet!"

    body_key = f"player_body_{player_id}"
    old_location = f"{current_zone}/{current_subzone}"
    allowed_targets = player_body = game.game_objects[current_zone][current_subzone][body_key].state["allowed_moves"]

    # Check if target is a subzone in the current zone
    if current_zone in game.zones["zones"] and target in game.zones["zones"][current_zone]["subzones"]:
        new_subzone = target
        if target not in allowed_targets:
            return "You are not allowed to move there!"
        game.player_locations[player_id]["subzone"] = new_subzone
        
        # Move player body object
        if body_key in game.game_objects[current_zone][current_subzone]:
            player_body = game.game_objects[current_zone][current_subzone].pop(body_key)
            game.game_objects[current_zone][new_subzone][body_key] = player_body
            if current_zone in game.engine_game_objects.keys() and new_subzone in game.engine_game_objects[current_zone].keys():
                await game.engine_game_objects[current_zone][current_subzone].remove_game_object(body_key)
                await game.engine_game_objects[current_zone][new_subzone].add_active_game_object(body_key, player_body)
                player_body.state["subzone"] = new_subzone
                #Move player body inventory objects
                if "inventory" in player_body.state.keys():
                    player_items = player_body.state["inventory"]
                    for item_name in player_items:
                        try:
                            item_object = await game.engine_game_objects[current_zone][current_subzone].remove_game_object(item_name)
                            await game.engine_game_objects[current_zone][new_subzone].add_active_game_object(item_name, item_object)
                            item_object = game.game_objects[current_zone][current_subzone].pop(item_name)
                            game.game_objects[current_zone][new_subzone][item_name] = item_object
                            await item_object.update_state({"zone":current_zone, "subzone":new_subzone})
                        except Exception as e:
                            print (e)
                            print ("could not move item with item key {item_name}")
                            
                    
        
        subzone_data = game.zones["zones"][current_zone]["subzones"][new_subzone]
        desc = subzone_data.get("short_description")
        return f"Moved from {old_location} to {current_zone}/{new_subzone}: {desc}"
    
    # Check if target is a different zone
    elif target in game.zones["zones"]:
        new_zone = target
        if target not in allowed_targets:
            return "You are not allowed to move there!"
        new_subzone = list(game.zones["zones"][new_zone]["subzones"].keys())[0]  # Default to first subzone
        game.player_locations[player_id]["zone"] = new_zone
        game.player_locations[player_id]["subzone"] = new_subzone
        await game.ensure_zone_initialized(new_zone, new_subzone)
        
        # Move player body object
        if current_zone in game.game_objects and current_subzone in game.game_objects[current_zone] and body_key in game.game_objects[current_zone][current_subzone]:
            player_body = game.game_objects[current_zone][current_subzone].pop(body_key)
            if new_zone not in game.game_objects:
                game.game_objects[new_zone] = {}
            if new_subzone not in game.game_objects[new_zone]:
                game.game_objects[new_zone][new_subzone] = {}
            game.game_objects[new_zone][new_subzone][body_key] = player_body
            if new_zone in game.engine_game_objects and new_subzone in game.engine_game_objects[new_zone]:
                await game.engine_game_objects[current_zone][current_subzone].remove_game_object(body_key)
                await game.engine_game_objects[new_zone][new_subzone].add_active_game_object(body_key, player_body)
                player_body.state["subzone"] = new_subzone
                player_body.state["zone"] = new_zone
                #Move player body inventory objects
                if "inventory" in player_body.state.keys():
                    player_items = player_body.state["inventory"]
                    for item_name in player_items:
                        try:
                            item_object = await game.engine_game_objects[current_zone][current_subzone].remove_game_object(item_name)
                            await game.engine_game_objects[new_zone][new_subzone].add_active_game_object(item_name)
                            item_object = game.game_objects[current_zone][current_subzone].pop(item_name)
                            game.game_objects[new_zone][new_subzone][item_name] = item_object
                            item_object.update_state({"zone":new_zone, "subzone":new_subzone})
                        except e:
                            print (e)
                            print ("could not move item with item key {item_name}")
                
        zone_desc = game.zones["zones"][new_zone].get("description", "An unknown land")
        subzone_data = game.zones["zones"][new_zone]["subzones"][new_subzone]
        subzone_desc = subzone_data.get("short_description", "A new place")
        return f"Moved from {old_location} to {new_zone}/{new_subzone}: {zone_desc} - {subzone_desc}"
    
    else:
        return "Invalid destination!"