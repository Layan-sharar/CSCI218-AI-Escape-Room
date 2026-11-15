import heapq
import random

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


# ---- Person D: dungeon levels ----

# Coordinates use (row, column). A 0 is floor and a 1 is a wall.
GRID_ROWS = 25
GRID_COLUMNS = 47

ROOMS = [
    # Upper rooms, side rooms, central hall, and three lower chambers.
    (1, 7, 1, 19),
    (1, 7, 27, 45),
    (9, 15, 1, 16),
    (9, 15, 18, 28),
    (9, 15, 30, 45),
    (18, 23, 1, 14),
    (18, 23, 18, 28),
    (18, 23, 32, 45),
]

STATIC_BLOCKING_FIELDS = (
    "spike_traps",
    "water_tiles",
    "crates",
    "barrels",
    "bookcases",
    "tables",
    "chests",
    "clay_pots",
    "chest_stacks",
    "gold_chests",
)


def _carve_maze_room(grid, bounds, seed):
    """Carve a connected maze with loops inside one room."""
    top, bottom, left, right = bounds
    rows = list(range(top + 1, bottom, 2))
    columns = list(range(left + 1, right, 2))
    row_set = set(rows)
    column_set = set(columns)
    rng = random.Random(seed)

    start = (rows[0], columns[0])
    visited = {start}
    stack = [start]
    grid[start[0]][start[1]] = 0

    while stack:
        row, column = stack[-1]
        neighbors = [
            (row - 2, column),
            (row + 2, column),
            (row, column - 2),
            (row, column + 2),
        ]
        rng.shuffle(neighbors)

        for next_row, next_column in neighbors:
            if next_row not in row_set or next_column not in column_set:
                continue
            if (next_row, next_column) in visited:
                continue

            grid[(row + next_row) // 2][(column + next_column) // 2] = 0
            grid[next_row][next_column] = 0
            visited.add((next_row, next_column))
            stack.append((next_row, next_column))
            break
        else:
            stack.pop()

    # Open some maze walls to add alternate routes around blockers.
    for row in rows:
        for column in columns:
            for next_row, next_column in ((row + 2, column), (row, column + 2)):
                if next_row not in row_set or next_column not in column_set:
                    continue
                middle_row = (row + next_row) // 2
                middle_column = (column + next_column) // 2
                if grid[middle_row][middle_column] == 1 and rng.random() < 0.12:
                    grid[middle_row][middle_column] = 0


def _carve_horizontal(grid, row, start_column, end_column):
    for column in range(start_column, end_column + 1):
        grid[row][column] = 0


def _carve_vertical(grid, column, start_row, end_row):
    for row in range(start_row, end_row + 1):
        grid[row][column] = 0


def _make_grid(left_passage=8, lower_right_passage=38, seed=1):
    """Build eight rooms, each with its own winding labyrinth."""
    grid = [[1 for _ in range(GRID_COLUMNS)] for _ in range(GRID_ROWS)]

    for room_number, bounds in enumerate(ROOMS):
        _carve_maze_room(grid, bounds, seed + room_number * 97)

    # Upper-left maze connects to the left-side trap chamber.
    _carve_vertical(grid, left_passage, 7, 10)

    # The guarded upper bridge leads from the central hall to the puzzle room.
    _carve_horizontal(grid, 3, 23, 28)
    _carve_vertical(grid, 23, 3, 10)

    # Winding central connections between the three middle rooms.
    _carve_horizontal(grid, 12, 15, 21)
    _carve_horizontal(grid, 12, 25, 31)

    # The lower rooms connect through narrow passages and a cross-hall.
    _carve_vertical(grid, left_passage, 15, 19)
    _carve_vertical(grid, 23, 15, 19)
    _carve_vertical(grid, lower_right_passage, 15, 19)
    _carve_horizontal(grid, 20, 12, 34)

    return grid


POOL_STONES = [(21, 21), (21, 23), (21, 25)]
POOL_WATER = [
    (row, column)
    for row in (21, 22)
    for column in range(20, 27)
    if (row, column) not in POOL_STONES
]

ROOM_DECORATIONS = {
    "clay_pots": [(4, 6)],
    "potions": [(4, 16), (10, 35), (10, 37)],
    "desk_scrolls": [(6, 14), (14, 35)],
    "open_books": [(12, 35)],
    "desk_candles": [(6, 14), (12, 35)],
    "crystals": [(2, 36)],
    "pressure_plates": [
        ((4, 32), "diamond"),
        ((4, 36), "triangle"),
        ((6, 32), "square"),
        ((6, 36), "circle"),
        ((12, 5), "square"),
        ((12, 11), "diamond"),
    ],
    "skeletons": [(6, 40)],
    "chest_stacks": [(2, 44)],
    "globes": [(10, 33)],
    "padlocked_doors": [(8, 38)],
    "pickaxes": [(21, 9)],
    "ladders": [(19, 8)],
    "rocks": [(21, 2)],
    "small_chests": [(21, 12)],
    "fountains": [(20, 20), (20, 26)],
    "barred_gates": [(20, 23)],
    "skulls": [(22, 18), (22, 28), (22, 2), (21, 10)],
    "center_statues": [(11, 21), (13, 25)],
    "treasure_statues": [(20, 35), (20, 41)],
    "gold_chests": [(21, 37)],
    "coins": [
        (22, 35), (22, 36), (22, 37), (22, 38),
        (22, 40), (21, 41), (22, 42),
    ],
}

LEVEL_1 = {
    "name": "The Ember Crypt Labyrinth",
    "grid": _make_grid(left_passage=8, lower_right_passage=38, seed=21),
    "start": (12, 23),
    "key": (4, 4),
    "door": (8, 23),
    "puzzle": (4, 36),
    "exit": (21, 43),
    "spike_traps": [
        (2, 2), (2, 18), (6, 2), (6, 18),
        (2, 28), (2, 44), (6, 28), (6, 44),
        (10, 2), (10, 14), (14, 2), (14, 14),
        (10, 19), (10, 27), (14, 19), (14, 27),
        (10, 31), (10, 43), (14, 31), (14, 43),
        (19, 2), (19, 12), (21, 2), (21, 12),
        (19, 19), (19, 27), (21, 19), (21, 27),
        (19, 33), (19, 43), (21, 33),
        (12, 6), (12, 10),
    ],
    "crates": [
        (2, 14), (6, 16), (14, 10), (19, 10), (2, 40), (19, 41),
        (14, 33), (21, 7),
    ],
    "barrels": [(6, 4), (6, 6), (21, 4), (21, 6), (10, 4)],
    "bookcases": [(4, 10), (12, 41), (14, 41)],
    "tables": [(6, 14), (12, 35)],
    "chests": [],
    "bones": [(12, 4), (4, 32), (14, 37), (21, 11), (21, 35)],
    "cobwebs": [(2, 4), (21, 10)],
    "water_tiles": POOL_WATER,
    "stepping_stones": POOL_STONES,
    "banners": [(2, 32), (2, 42), (10, 21), (10, 25), (19, 35), (19, 41)],
    "torches": [
        (2, 8), (6, 8), (2, 36), (6, 36),
        (10, 8), (14, 8), (10, 37), (14, 37),
        (10, 20), (10, 26), (14, 20), (14, 26),
        (19, 8), (21, 8), (19, 21), (19, 25),
        (19, 37), (21, 37),
    ],
    **ROOM_DECORATIONS,
}

LEVEL_2 = {
    "name": "The Lower Crypt Labyrinth",
    "grid": _make_grid(left_passage=6, lower_right_passage=40, seed=77),
    "start": (12, 23),
    "key": (21, 4),
    "door": (8, 23),
    "puzzle": (4, 36),
    "exit": (21, 43),
    "spike_traps": [
        (2, 4), (2, 16), (6, 4), (6, 16),
        (2, 30), (2, 42), (6, 30), (6, 42),
        (10, 2), (10, 12), (14, 2), (14, 12),
        (10, 19), (10, 27), (14, 19), (14, 27),
        (10, 31), (10, 41), (14, 31), (14, 41),
        (19, 2), (19, 12), (21, 2), (21, 12),
        (19, 19), (19, 27), (21, 19), (21, 27),
        (19, 33), (19, 43), (21, 33), (21, 37),
        (12, 6), (12, 10),
    ],
    "crates": [
        (2, 14), (6, 16), (14, 10), (19, 10), (2, 40), (19, 41),
        (14, 33), (21, 7),
    ],
    "barrels": [(6, 4), (6, 8), (21, 2), (21, 6), (10, 4)],
    "bookcases": [(4, 10), (12, 41), (14, 41)],
    "tables": [(6, 14), (12, 35)],
    "chests": [],
    "bones": [(12, 4), (4, 32), (14, 37), (21, 11), (21, 35)],
    "cobwebs": [(2, 4), (21, 10)],
    "water_tiles": POOL_WATER,
    "stepping_stones": POOL_STONES,
    "banners": [(2, 32), (2, 42), (10, 21), (10, 25), (19, 35), (19, 41)],
    "torches": [
        (2, 8), (6, 8), (2, 36), (6, 36),
        (10, 8), (14, 8), (10, 37), (14, 37),
        (10, 20), (10, 26), (14, 20), (14, 26),
        (19, 8), (21, 8), (19, 21), (19, 25),
        (19, 37), (21, 37),
    ],
    **ROOM_DECORATIONS,
}


def _carve_route(grid, start, targets, blocked):
    """Connect objectives while strongly favoring existing corridors."""
    targets = {tuple(target) for target in targets if tuple(target) not in blocked}
    if not targets:
        return False

    frontier = [(0, start)]
    costs = {start: 0}
    previous = {start: None}
    destination = None

    while frontier:
        cost, position = heapq.heappop(frontier)
        if cost != costs[position]:
            continue
        if position in targets:
            destination = position
            break

        row, column = position
        for neighbor in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            next_row, next_column = neighbor
            if (
                not 1 <= next_row < len(grid) - 1
                or not 1 <= next_column < len(grid[next_row]) - 1
                or neighbor in blocked
            ):
                continue

            # Existing corridors are cheaper so the maze keeps its winding paths.
            step_cost = 1 if grid[next_row][next_column] == 0 else 12
            next_cost = cost + step_cost
            if next_cost < costs.get(neighbor, float("inf")):
                costs[neighbor] = next_cost
                previous[neighbor] = position
                heapq.heappush(frontier, (next_cost, neighbor))

    if destination is None:
        return False

    position = destination
    while position is not None:
        row, column = position
        grid[row][column] = 0
        position = previous[position]
    return True


def _connect_level_objectives(level):
    """Ensure obstacles never seal the route through this labyrinth."""
    grid = [row[:] for row in level["grid"]]
    blocked = {
        position
        for field in STATIC_BLOCKING_FIELDS
        for position in level.get(field, [])
    }
    door = level["door"]
    blocked_before_door = blocked | {door}

    if not _carve_route(grid, level["start"], [level["key"]], blocked_before_door):
        raise ValueError(f"No route to the key in {level['name']}.")

    door_row, door_column = door
    door_neighbors = [
        (door_row - 1, door_column),
        (door_row + 1, door_column),
        (door_row, door_column - 1),
        (door_row, door_column + 1),
    ]
    if not _carve_route(grid, level["start"], door_neighbors, blocked_before_door):
        raise ValueError(f"No route to the locked door in {level['name']}.")

    if not _carve_route(grid, level["start"], [level["puzzle"]], blocked):
        raise ValueError(f"No route to the puzzle in {level['name']}.")
    if not _carve_route(grid, level["puzzle"], [level["exit"]], blocked):
        raise ValueError(f"No route from the puzzle to the exit in {level['name']}.")

    level["grid"] = grid


_connect_level_objectives(LEVEL_1)
_connect_level_objectives(LEVEL_2)

LEVELS = {
    "ember_crypt": LEVEL_1,
    "lower_crypt": LEVEL_2,
}


def get_level(level_id):
    """Return a level by ID, such as 'ember_crypt'."""
    return LEVELS[level_id]


def get_grid(level_id):
    """Return a separate copy of a level's floor-and-wall grid."""
    return [row[:] for row in get_level(level_id)["grid"]]


def get_static_blocked_cells(level_id):
    """Return the cells occupied by fixed traps and objects."""
    level = get_level(level_id)
    return {
        position
        for field in STATIC_BLOCKING_FIELDS
        for position in level.get(field, [])
    }


def is_walkable_in_level(level_id, position):
    """Check whether a cell is open floor without a fixed obstacle."""
    position = tuple(position)
    row, column = position
    grid = get_grid(level_id)

    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False

    return grid[row][column] == 0 and position not in get_static_blocked_cells(level_id)
