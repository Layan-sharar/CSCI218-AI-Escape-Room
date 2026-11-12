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