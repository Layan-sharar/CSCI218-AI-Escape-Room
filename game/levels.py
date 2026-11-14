
# 1 = wall/barrier, 0 = walkable floor
# Access using test_grid[row][col]

test_grid = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Screen dimensions
screen_width = 800
screen_height = 800

# Robot dimensions (must match renderer.py)
robot_width = 80
robot_height = 80

# Grid dimensions
rows = len(test_grid)
cols = len(test_grid[0])

cell_height = screen_height / rows
cell_width = screen_width / cols


def grid_to_pixel(row, col):
    """Convert grid coordinates to pixel coordinates,
    centering the robot inside its cell."""

    x = col * cell_width + (cell_width - robot_width) / 2
    y = row * cell_height + (cell_height - robot_height) / 2

    return int(x), int(y)


def is_walkable(row, col):
    """Check whether a grid cell is inside the map and walkable."""

    if 0 <= row < rows and 0 <= col < cols:
        return test_grid[row][col] == 0

    return False
