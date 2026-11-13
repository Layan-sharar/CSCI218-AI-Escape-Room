from game.levels import get_grid


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
