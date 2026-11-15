import pygame

from game.levels import get_level

# Each grid cell is one 16px tile drawn at 2x
TILE_SIZE = 16
CELL_SIZE = 32

TILESET = "assets/tilesets/Dungeon_Tileset.png"

# (column, row) of each 16px tile in the tileset
TILES = {
    "floor": (6, 1),
    "wall": (2, 0),
    "door": (7, 3),
    "exit": (9, 3),
    "key": (9, 9),
    "puzzle": (4, 7),
    "torch": (0, 9),
    "crate": (3, 8),
    "chest": (4, 8),
    "table": (1, 8),
    "rocks": (9, 4),
}

# Blocking props in the level data and the tile drawn for each
PROP_TILES = {
    "crates": "crate",
    "barrels": "crate",
    "chests": "chest",
    "gold_chests": "chest",
    "chest_stacks": "chest",
    "bookcases": "table",
    "tables": "table",
    "clay_pots": "rocks",
}

WATER_COLOUR = (40, 80, 140)

# Filled in by load_assets() once the window exists
tiles = {}
spike_frames = {}
idle_frames = []
walk_frames = {}
_backgrounds = {}


def window_size(level_id):
    """Pixel size of the window needed to show a level."""
    grid = get_level(level_id)["grid"]
    return len(grid[0]) * CELL_SIZE, len(grid) * CELL_SIZE


def grid_to_pixel(row, col):
    """Top-left pixel of a grid cell (the robot is the same size as a cell)."""
    return col * CELL_SIZE, row * CELL_SIZE


def scaled(image):
    return pygame.transform.scale(image, (CELL_SIZE, CELL_SIZE))


# Function to load robot animation frames
def load_animation(action, direction, frame_count):
    frames = []

    for i in range(frame_count):
        frame = pygame.image.load(
            f"assets/sprites/robot/frames/helper_robot_{action}_{direction}_{i:02d}.png"
        ).convert_alpha()

        frames.append(scaled(frame))

    return frames


def load_assets():
    """Load every image. Call after pygame.display.set_mode()."""
    global idle_frames

    tileset = pygame.image.load(TILESET).convert_alpha()
    for name, (col, row) in TILES.items():
        rect = (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        tiles[name] = scaled(tileset.subsurface(rect))

    for i in range(1, 5):
        frame = pygame.image.load(f"assets/sprites/traps/peaks_{i}.png").convert_alpha()
        spike_frames[i] = scaled(frame)

    # Load idle animation
    idle_frames = load_animation("idle", "south", 4)

    # Load walking animations
    for direction in ("north", "south", "east", "west"):
        walk_frames[direction] = load_animation("walk", direction, 6)


def background(level_id):
    """Floor, walls and fixed props, drawn once per level."""
    if level_id not in _backgrounds:
        level = get_level(level_id)
        surface = pygame.Surface(window_size(level_id))

        for row, cells in enumerate(level["grid"]):
            for col, cell in enumerate(cells):
                tile = tiles["wall" if cell else "floor"]
                surface.blit(tile, grid_to_pixel(row, col))

        for row, col in level.get("water_tiles", []):
            x, y = grid_to_pixel(row, col)
            surface.fill(WATER_COLOUR, (x, y, CELL_SIZE, CELL_SIZE))

        # Fixed spike traps are always up
        for position in level.get("spike_traps", []):
            surface.blit(spike_frames[1], grid_to_pixel(*position))

        for field, tile in PROP_TILES.items():
            for position in level.get(field, []):
                surface.blit(tiles[tile], grid_to_pixel(*position))

        for position in level.get("torches", []):
            surface.blit(tiles["torch"], grid_to_pixel(*position))

        surface.blit(tiles["exit"], grid_to_pixel(*level["exit"]))
        _backgrounds[level_id] = surface

    return _backgrounds[level_id]


def draw_level(screen, state):
    """Draw the level plus the objects whose look depends on the world state."""
    screen.blit(background(state.level_id), (0, 0))

    if not state.door_unlocked:
        screen.blit(tiles["door"], grid_to_pixel(*state.door_position))

    if not state.has_key:
        screen.blit(tiles["key"], grid_to_pixel(*state.key_position))

    if not state.puzzle_solved:
        screen.blit(tiles["puzzle"], grid_to_pixel(*state.puzzle_position))


def draw_path(screen, path, colour=(90, 200, 255)):
    """Mark the planned A* route with small squares."""
    size = CELL_SIZE // 4

    for row, col in path or []:
        x, y = grid_to_pixel(row, col)
        offset = (CELL_SIZE - size) // 2
        pygame.draw.rect(screen, colour, (x + offset, y + offset, size, size))
