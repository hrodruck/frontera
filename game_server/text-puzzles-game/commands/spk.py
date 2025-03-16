async def handle_spk(game, player_id, args):
    """Handle freeform !spk commands."""
    if not args:
        return "Please provide an action after !spk (e.g., !spk Look around)"
    return args  # Pass raw input to engine for processing