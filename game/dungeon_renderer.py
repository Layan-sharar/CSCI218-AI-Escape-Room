from pathlib import Path

import pygame

from game.levels import get_level


TILE_SIZE = 16
SCALE = 2
CELL_SIZE = TILE_SIZE * SCALE

MAP_WIDTH = 47
MAP_HEIGHT = 25
MARGIN_X = 24
MAP_TOP = 70

WINDOW_WIDTH = MARGIN_X * 2 + MAP_WIDTH * CELL_SIZE
WINDOW_HEIGHT = MAP_TOP + MAP_HEIGHT * CELL_SIZE + 54

ASSET_DIR = (
    Path(__file__).resolve().parents[1]
    / "DungeonTileset_Free"
    / "DungeonTileset"
)
REFERENCE_IMAGE = Path(__file__).with_name("escape_room_reference_obstacles.png")


def crop_tile(sheet, column, row):
    """Copy one 16-by-16 tile from a sprite sheet."""
    rectangle = pygame.Rect(
        column * TILE_SIZE,
        row * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE,
    )
    return sheet.subsurface(rectangle).copy()


def load_sprites():
    """Load and enlarge the floor, wall, and prop tiles."""
    tileset_path = ASSET_DIR / "Tileset.png"
    props_path = ASSET_DIR / "Props&Items.png"

    if not tileset_path.exists() or not props_path.exists():
        raise FileNotFoundError(
            "Tileset images were not found. They should be in "
            "DungeonTileset_Free/DungeonTileset."
        )

    tileset = pygame.image.load(str(tileset_path)).convert_alpha()
    props = pygame.image.load(str(props_path)).convert_alpha()

    tile_parts = {
        "floor": crop_tile(tileset, 1, 1),
        "wall": crop_tile(tileset, 1, 0),
        "door": crop_tile(props, 0, 0),
        "spike": crop_tile(props, 0, 1),
        "torch": crop_tile(props, 0, 3),
        "key": crop_tile(props, 3, 2),
        "puzzle": crop_tile(props, 2, 2),
    }

    return {
        name: pygame.transform.scale(
            tile,
            (CELL_SIZE, CELL_SIZE),
        )
        for name, tile in tile_parts.items()
    }


def draw_sprite(screen, sprites, name, position):
    """Draw one enlarged sprite at a (row, column) position."""
    row, column = position
    x = MARGIN_X + column * CELL_SIZE
    y = MAP_TOP + row * CELL_SIZE
    screen.blit(sprites[name], (x, y))


def draw_player_marker(screen, position):
    """Draw a simple marker for the player's starting position."""
    row, column = position
    x = MARGIN_X + column * CELL_SIZE
    y = MAP_TOP + row * CELL_SIZE

    pygame.draw.rect(
        screen,
        (231, 183, 87),
        (x + 15, y + 12, 18, 27),
    )
    pygame.draw.rect(
        screen,
        (43, 30, 54),
        (x + 19, y + 16, 10, 8),
    )


def draw_level(screen, sprites, level_id):
    """Draw the map and its themed props."""
    level = get_level(level_id)

    for row_index, row in enumerate(level["grid"]):
        for column_index, cell in enumerate(row):
            tile_name = "floor" if cell == 0 else "wall"
            position = (row_index, column_index)
            draw_sprite(screen, sprites, tile_name, position)

    for position in level.get("spike_traps", []):
        draw_sprite(screen, sprites, "spike", position)

    for position in level.get("torches", []):
        draw_sprite(screen, sprites, "torch", position)

    draw_sprite(screen, sprites, "door", level["door"])
    draw_sprite(screen, sprites, "key", level["key"])
    draw_sprite(screen, sprites, "puzzle", level["puzzle"])
    draw_sprite(screen, sprites, "door", level["exit"])
    draw_player_marker(screen, level["start"])


def main():
    pygame.init()
    reference = pygame.image.load(str(REFERENCE_IMAGE))
    image_width, image_height = reference.get_size()
    display = pygame.display.Info()
    screen_width = max(320, min(1280, display.current_w - 80)) if display.current_w > 0 else 1280
    screen_height = max(240, min(720, display.current_h - 120)) if display.current_h > 0 else 720
    scale = min(0.8, screen_width / image_width, screen_height / image_height)
    view_size = (int(image_width * scale), int(image_height * scale))
    reference = pygame.transform.smoothscale(reference, view_size)
    screen = pygame.display.set_mode(view_size)
    reference = reference.convert()
    pygame.display.set_caption("Pixel Dungeon Escape Room")

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.blit(reference, (0, 0))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
