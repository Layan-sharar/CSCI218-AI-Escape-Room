from pathlib import Path

import pygame

from game.levels import get_level


TILE_SIZE = 16
SCALE = 3
CELL_SIZE = TILE_SIZE * SCALE

MAP_WIDTH = 9
MAP_HEIGHT = 7
MARGIN_X = 24
MAP_TOP = 84

WINDOW_WIDTH = MARGIN_X * 2 + MAP_WIDTH * CELL_SIZE
WINDOW_HEIGHT = MAP_TOP + MAP_HEIGHT * CELL_SIZE + 54

ASSET_DIR = (
    Path(__file__).resolve().parents[1]
    / "DungeonTileset_Free"
    / "DungeonTileset"
)


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
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Pixel Dungeon Escape Room")

    try:
        sprites = load_sprites()
    except FileNotFoundError as error:
        pygame.quit()
        raise SystemExit(str(error))

    title_font = pygame.font.Font(None, 30)
    hint_font = pygame.font.Font(None, 21)
    current_level = "ember_crypt"
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    current_level = "ember_crypt"
                elif event.key == pygame.K_2:
                    current_level = "lower_crypt"

        screen.fill((24, 19, 37))

        level = get_level(current_level)
        title = title_font.render(level["name"], True, (235, 220, 190))
        hint = hint_font.render(
            "Press 1 or 2 to view a level. Close the window to exit.",
            True,
            (200, 190, 210),
        )

        screen.blit(title, (MARGIN_X, 18))
        screen.blit(hint, (MARGIN_X, 52))

        draw_level(screen, sprites, current_level)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()