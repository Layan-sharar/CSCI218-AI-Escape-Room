 person-d-world-rules
import heapq
import random

# Coordinates use (row, column). A 0 is floor and a 1 is a wall.

# Reference-inspired RogueMind level layout.
# This version keeps the same world-state fields and AI expectations,
# but replaces the loose maze with a fixed, room-based dungeon layout.

 main
GRID_ROWS = 25
GRID_COLUMNS = 47

ROOMS = [
 person-d-world-rules
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

    (1, 7, 1, 19),    # upper-left archive
    (1, 7, 27, 45),   # upper-right puzzle chamber
    (9, 15, 1, 16),   # middle-left spike chamber
    (9, 15, 18, 28),  # central chamber
    (9, 15, 30, 45),  # middle-right study
    (18, 23, 1, 14),  # lower-left storage
    (18, 23, 18, 28), # lower-middle flooded room
    (18, 23, 32, 45), # lower-right treasury / exit
]

STATIC_BLOCKING_FIELDS = (
 main
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


 person-d-world-rules
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

def _wall_grid():
    return [[1 for _ in range(GRID_COLUMNS)] for _ in range(GRID_ROWS)]


def _carve_room(grid, top, bottom, left, right):
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            grid[row][col] = 0


def _carve_h(grid, row, start_col, end_col):
    for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
        grid[row][col] = 0


def _carve_v(grid, col, start_row, end_row):
    for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
        grid[row][col] = 0


def _carve_rect(grid, top, bottom, left, right):
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            grid[row][col] = 0


def _add_inner_wall(grid, top, bottom, left, right):
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            grid[row][col] = 1


def _make_reference_grid(level_variant=1):
    """Build a fixed room layout close to the reference image."""
    grid = _wall_grid()

    # Open all main chambers.
    for bounds in ROOMS:
        _carve_room(grid, *bounds)

    # Central vertical axis.
    _carve_v(grid, 23, 3, 18)

    # Left-hand route: center -> spike room -> upper-left key room.
    _carve_h(grid, 12, 16, 18)
    _carve_v(grid, 8, 7, 18)

    # Right-hand room directly beside the center.
    _carve_h(grid, 12, 28, 30)

    # Door / puzzle route only through the north connector.
    _carve_h(grid, 8, 22, 24)
    _carve_v(grid, 31, 3, 6)
    _carve_h(grid, 3, 23, 31)

    # Lower route: center -> water room -> exit room.
    _carve_h(grid, 16, 22, 24)
    _carve_h(grid, 20, 28, 32)

    # Lower-left storage connection.
    _carve_v(grid, 8, 15, 18)

    # Decorative alcove hints similar to the reference, without blocking the route.
    if level_variant == 2:
        _carve_rect(grid, 4, 4, 3, 15)
        _carve_rect(grid, 20, 20, 20, 26)
 main

    return grid


 person-d-world-rules
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

=======
# Water crossing from the reference style: short visible pool with safe stones.
POOL_STONES = [(19, 23)] + [(20, col) for col in range(20, 28)]
POOL_WATER = [
    (row, column)
    for row in (19, 20, 21)
    for column in range(19, 28)
    if (row, column) not in POOL_STONES
]

BASE_DECOR = {
    "clay_pots": [(4, 29)],
    "potions": [(4, 15), (10, 34)],
    "desk_scrolls": [(5, 13), (12, 37)],
    "open_books": [(12, 36)],
    "desk_candles": [(5, 13), (12, 36)],
    "crystals": [(2, 35)],
    # Visible switches match all five variables in puzzles/switch_puzzle.py.
    # These are visual controls; CSP and interaction rules remain unchanged.
    "pressure_plates": [
        ((4, 33), "RED"),
        ((4, 35), "BLUE"),
        ((4, 37), "GREEN"),
        ((6, 33), "YELLOW"),
        ((6, 35), "WHITE"),
    ],
    "skeletons": [(6, 41)],
    "chest_stacks": [(3, 43)],
    # removed: decorative extra locked doors
    "pickaxes": [(21, 5)],
    "ladders": [(19, 7)],
    "rocks": [(21, 2)],
    "small_chests": [(22, 3)],
    "fountains": [(19, 19), (19, 27)],
    "skulls": [(13, 3), (21, 9), (21, 18), (21, 29)],
    "center_statues": [(11, 20), (11, 26)],
    "treasure_statues": [(20, 33), (20, 44)],
    "gold_chests": [(20, 38)],
    # removed: coins
}

LEVEL_1 = {
    "name": "The Ember Crypt",
    "grid": _make_reference_grid(1),
    "start": (12, 23),
    "key": (4, 4),
    "door": (8, 23),
    "puzzle": (5, 37),
    "exit": (21, 43),
    "spike_traps": [
        (11, 4), (11, 5), (11, 6),
        (11, 10), (11, 11), (11, 12),
        (10, 8), (12, 8),
        (4, 3), (4, 17),
        (10, 19), (10, 27),
        (10, 32), (10, 43),
        (14, 8), (14, 20), (14, 26), (14, 37),
        (19, 8), (19, 20), (19, 26), (19, 37),
        (20, 37), (21, 8), (21, 37), (22, 37),
    ],
    "crates": [(3, 6), (3, 8), (3, 16), (5, 16), (20, 10), (21, 10), (21, 11)],
    "barrels": [(5, 2), (6, 2), (6, 4), (20, 3), (20, 4)],
    "bookcases": [(3, 11), (5, 15), (12, 41)],
    "tables": [(5, 11), (12, 36)],
    "chests": [],
    "bones": [(6, 39), (13, 12), (21, 6)],
    "cobwebs": [(3, 1), (19, 1)],
    "water_tiles": POOL_WATER,
    "stepping_stones": POOL_STONES,
    "banners": [(2, 32), (2, 40), (9, 22), (9, 24), (19, 35), (19, 40)],
    "torches": [
        (2, 4), (2, 17), (2, 31), (2, 43),
        (10, 2), (10, 15), (10, 31), (10, 44),
        (10, 22), (10, 24), (10, 37),
        (19, 2), (19, 8), (19, 18), (19, 28), (19, 39), (19, 43),
    ],
    **BASE_DECOR,
}

LEVEL_2 = {
    "name": "The Lower Crypt",
    "grid": _make_reference_grid(2),
    "start": (12, 23),
    "key": (21, 3),
    "door": (8, 23),
    "puzzle": (5, 37),
    "exit": (21, 43),
    "spike_traps": [
        (10, 4), (10, 5), (10, 6),
        (11, 10), (12, 11), (11, 12),
        (11, 8), (13, 11),
        (4, 5), (4, 14),
        (10, 19), (10, 27),
        (10, 32), (10, 43),
        (14, 8), (14, 20), (14, 26), (14, 37),
        (19, 8), (19, 20), (19, 26), (19, 37),
        (20, 37), (21, 8), (21, 37), (22, 37),
    ],
    "crates": [(3, 6), (3, 8), (3, 16), (5, 16), (20, 10), (21, 10), (21, 11)],
    "barrels": [(5, 2), (6, 2), (6, 4), (20, 3), (20, 4)],
    "bookcases": [(3, 11), (5, 15), (12, 41)],
    "tables": [(5, 11), (12, 36)],
    "chests": [],
    "bones": [(6, 39), (13, 12), (21, 6)],
    "cobwebs": [(3, 1), (19, 1)],
    "water_tiles": POOL_WATER,
    "stepping_stones": POOL_STONES,
    "banners": [(2, 32), (2, 40), (9, 22), (9, 24), (19, 35), (19, 40)],
    "torches": [
        (2, 4), (2, 17), (2, 31), (2, 43),
        (10, 2), (10, 15), (10, 31), (10, 44),
        (10, 22), (10, 24), (10, 37),
        (19, 2), (19, 8), (19, 18), (19, 28), (19, 39), (19, 43),
    ],
    **BASE_DECOR,
}

 main
LEVELS = {
    "ember_crypt": LEVEL_1,
    "lower_crypt": LEVEL_2,
}


def get_level(level_id):
 person-d-world-rules
    """Return a level by ID, such as 'ember_crypt'."""

 main
    return LEVELS[level_id]


def get_grid(level_id):
 person-d-world-rules
    """Return a separate copy of a level's floor-and-wall grid."""

 main
    return [row[:] for row in get_level(level_id)["grid"]]


def get_static_blocked_cells(level_id):
person-d-world-rules
    """Return the cells occupied by fixed traps and objects."""

 main
    level = get_level(level_id)
    return {
        position
        for field in STATIC_BLOCKING_FIELDS
        for position in level.get(field, [])
    }


def is_walkable(level_id, position):
 person-d-world-rules
    """Check whether a cell is open floor without a fixed obstacle."""
    position = tuple(position)
    row, column = position
    grid = get_grid(level_id)


    row, column = tuple(position)
    grid = get_grid(level_id)
 main
    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False
 person-d-world-rules

    return grid[row][column] == 0 and position not in get_static_blocked_cells(level_id)

    return grid[row][column] == 0 and (row, column) not in get_static_blocked_cells(level_id)
 main
