from game.levels import get_grid


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


def move_player(state, new_position):
    """Move one tile if the destination is inside the map and unblocked."""
    current_row, current_column = state.player_position
    new_row, new_column = new_position

    # Only allow a move to one neighboring tile.
    distance = abs(new_row - current_row) + abs(new_column - current_column)
    if distance != 1:
        return False

    grid = state.get_ai_grid()

    # Reject positions outside the map.
    if new_row < 0 or new_row >= len(grid):
        return False
    if new_column < 0 or new_column >= len(grid[new_row]):
        return False

    # 1 means blocked: a wall or a locked door.
    if grid[new_row][new_column] == 1:
        return False

    state.player_position = (new_row, new_column)
    return True


def set_dynamic_obstacle(state, position, blocked=True):
    """Block or unblock a floor cell for a changing obstacle."""
    grid = get_grid(state.level_id)

    try:
        row, column = position
    except (TypeError, ValueError):
        return False

    if not isinstance(row, int) or not isinstance(column, int):
        return False

    # Only allow positions inside the map that are floor tiles.
    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False
    if grid[row][column] != 0:
        return False

    cell = (row, column)
    if blocked:
        state.dynamic_obstacles.add(cell)
    else:
        state.dynamic_obstacles.discard(cell)

    return True
