def collect_key(state):
    """Collect the key when the player reaches its position."""
    if state.has_key:
        return False

    if state.player_position != state.key_position:
        return False

    state.has_key = True
    return True
def unlock_door(state):
    """Unlock the door when the player has a key and stands beside it."""
    if state.door_unlocked or not state.has_key:
        return False

    player_row, player_column = state.player_position
    door_row, door_column = state.door_position

    # The locked door blocks its own tile, so unlock it from a neighboring tile.
    distance = abs(player_row - door_row) + abs(player_column - door_column)
    if distance != 1:
        return False

    state.door_unlocked = True
    return True
def complete_puzzle(state, answer_is_correct):
    """Mark the puzzle solved only after its logic confirms the answer."""
    if state.puzzle_solved or not state.door_unlocked:
        return False

    if state.player_position != state.puzzle_position:
        return False

    if not answer_is_correct:
        return False

    state.puzzle_solved = True
    return True
def complete_level(state):
    """Finish the level when the player reaches an open exit."""
    if state.level_complete:
        return False

    if not state.exit_open:
        return False

    if state.player_position != state.exit_position:
        return False

    state.level_complete = True
    return True