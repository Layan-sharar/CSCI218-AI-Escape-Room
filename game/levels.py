# Reference-inspired RogueMind level layout.
# This version keeps the same world-state fields and AI expectations,
# but replaces the loose maze with a fixed, room-based dungeon layout.

GRID_ROWS = 25
GRID_COLUMNS = 47

ROOMS = [
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

    return grid


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

LEVELS = {
    "ember_crypt": LEVEL_1,
    "lower_crypt": LEVEL_2,
}


def get_level(level_id):
    return LEVELS[level_id]


def get_grid(level_id):
    return [row[:] for row in get_level(level_id)["grid"]]


def get_static_blocked_cells(level_id):
    level = get_level(level_id)
    return {
        position
        for field in STATIC_BLOCKING_FIELDS
        for position in level.get(field, [])
    }


def is_walkable(level_id, position):
    row, column = tuple(position)
    grid = get_grid(level_id)
    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False
    return grid[row][column] == 0 and (row, column) not in get_static_blocked_cells(level_id)
