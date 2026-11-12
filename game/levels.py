# 0 = walkable floor; 1 = wall
# Coordinates are written as (row, column).
LEVEL_1 = {
    "name": "The Ember Crypt",
    "grid": [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 1, 1, 1, 1],
        [1, 0, 1, 1, 0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    "start": (1, 1),
    "key": (1, 3),
    "door": (3, 4),
    "puzzle": (3, 6),
    "exit": (5, 7),
}
LEVEL_2 = {
    "name": "The Lower Crypt",
    "grid": [
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1, 1, 1, 1, 1],
        [1, 1, 1, 0, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    "start": (1, 1),
    "key": (1, 2),
    "door": (3, 4),
    "puzzle": (3, 6),
    "exit": (5, 7),
}
LEVELS = {
    "ember_crypt": LEVEL_1,
    "lower_crypt": LEVEL_2,
}
def get_level(level_id):
    """Return a level using its ID, such as 'ember_crypt'."""
    return LEVELS[level_id]
def get_grid(level_id):
    """Return a separate copy of a level's 0/1 grid."""
    return [row[:] for row in get_level(level_id)["grid"]]
def is_walkable(level_id, position):
    """Check whether a position is floor in the static map."""
    row, column = position
    grid = get_grid(level_id)

    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False

    return grid[row][column] == 0
