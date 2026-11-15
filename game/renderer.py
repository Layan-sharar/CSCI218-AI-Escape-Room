"""Asset-only visual renderer for the team's original RogueMind level data.

All world layouts and collision rules remain in game.levels / game.state.
This module does not read or display the reference PNG. Every dungeon image
is cropped from the supplied 2D Pixel Dungeon Asset Pack v2.0 or loaded from
its animation files. Coordinates are the original (row, column) 47x25 grid.
"""
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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "assets"
TILESET_PATH = ASSET_DIR / "tilesets" / "Dungeon_Tileset.png"
ANIM_DIR = ASSET_DIR / "dungeon" / "animations"
TRAP_DIR = ASSET_DIR / "sprites" / "traps"

# Compatibility for code that reads the old display dimensions.
screen_width = WINDOW_WIDTH
screen_height = WINDOW_HEIGHT


def crop_tile(sheet, column, row):
    """Crop exactly one original 16x16 sprite, using (column, row)."""
    region = pygame.Rect(column * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    if not sheet.get_rect().contains(region):
        raise ValueError(f"Tile ({column}, {row}) outside the sprite sheet")
    return sheet.subsurface(region).copy()


def _scaled(sheet, col, row):
    return pygame.transform.scale(crop_tile(sheet, col, row), (CELL_SIZE, CELL_SIZE))


def _load_image(path, size=(CELL_SIZE, CELL_SIZE)):
    if not path.is_file():
        raise FileNotFoundError(f"Required asset missing: {path}")
    image = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.scale(image, size)


def _animation(folder, basename, frames=4):
    return tuple(
        _load_image(ANIM_DIR / folder / f"{basename}_{frame}.png")
        for frame in range(1, frames + 1)
    )


def _choose(variants, row, col):
    """Stable visual variation; does not change the generated level."""
    return variants[(row * 19 + col * 31 + row * col * 7) % len(variants)]


def load_sprites():
    """Load actual art once; called after pygame.display.set_mode()."""
    if not TILESET_PATH.is_file():
        raise FileNotFoundError(f"Missing Dungeon_Tileset.png: {TILESET_PATH}")
    sheet = pygame.image.load(str(TILESET_PATH)).convert_alpha()
    if sheet.get_size() != (160, 160):
        raise ValueError("Expected the provided 160x160 Dungeon_Tileset.png")

    tile = {(c, r): _scaled(sheet, c, r) for r in range(10) for c in range(10)}
    # Load only the original helper robot animations.
    robot_root = ASSET_DIR / "sprites" / "robot" / "frames"
    robot_frames = {}

    for direction in ("south", "north", "east", "west"):
        for action, count in (("idle", 4), ("walk", 6)):
            paths = [
                robot_root / f"helper_robot_{action}_{direction}_{i:02d}.png"
                for i in range(count)
            ]
            for path in paths:
                if not path.is_file():
                    raise FileNotFoundError(f"Missing robot animation frame: {path}")
            robot_frames[(action, direction)] = tuple(
                _load_image(path, (CELL_SIZE, CELL_SIZE)) for path in paths
            )

    return {
        "tile": tile,
        "robot": robot_frames,
        "spikes": {i: _load_image(TRAP_DIR / f"peaks_{i}.png") for i in range(1, 5)},
        "torches": _animation("torch", "torch"),
        "side_torches": _animation("torch", "side_torch"),
        "candles": _animation("torch", "candlestick_1"),
        "key": _animation("keys", "keys_1"),
        "chest": _animation("chest", "chest"),
        "flag": _animation("flag", "flag"),
        "potions": _animation("flasks", "flasks_1"),
        "crates": _animation("box_2", "box_2"),
        "small_crates": _animation("box_1", "box_1"),
    }


def grid_to_pixel(row, col):
    """Pixel top-left of a cell, matching RobotMovement without changing it."""
    return MARGIN_X + col * CELL_SIZE, MAP_TOP + row * CELL_SIZE


def draw_sprite(screen, sprites, name, position):
    """Backwards-compatible sprite helper for simple named tiles."""
    palette = {"floor": (7, 1), "wall": (2, 0), "door": (8, 3),
               "torch": (0, 9), "key": (7, 8), "puzzle": (3, 2),
               "spike": None}
    source = sprites["spikes"][1] if name == "spike" else sprites["tile"][palette[name]]
    screen.blit(source, grid_to_pixel(*position))


def _draw_image(screen, image, position):
    screen.blit(image, grid_to_pixel(*position))


def _draw_field(screen, level, field, image):
    for position in level.get(field, ()):
        _draw_image(screen, image, position)


def _anim(frames, tick_ms, step_ms=220):
    return frames[(tick_ms // step_ms) % len(frames)]


def _draw_background(screen, sprites, level):
    """Asset-based open room floors and masonry borders.

    Tiles follow the *same grid* used by WorldState/A*. The large empty blocks
    between rooms become shadowed void rather than an artificial brick maze.
    """
    grid = level["grid"]
    tiles = sprites["tile"]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            x, y = grid_to_pixel(row, col)
            if value == 0:
                floor_options = [(7, 1), (8, 1), (9, 1), (6, 1),
                                 (7, 2), (8, 2), (6, 2), (2, 1)]
                sprite = tiles[_choose(floor_options, row, col)]
            else:
                north = row > 0 and grid[row - 1][col] == 0
                south = row < len(grid) - 1 and grid[row + 1][col] == 0
                west = col > 0 and grid[row][col - 1] == 0
                east = col < len(values) - 1 and grid[row][col + 1] == 0
                if south:
                    sprite = tiles[(1 + (col % 4), 0)]
                elif north:
                    sprite = tiles[(1 + (col % 4), 4)]
                elif east and not west:
                    sprite = tiles[(0, 2 + (row % 2))]
                elif west and not east:
                    sprite = tiles[(5, 2 + (row % 2))]
                elif east or west:
                    sprite = tiles[(2 + (col % 2), 4)]
                else:
                    # Dark stone / void inside inaccessible world space.
                    sprite = tiles[_choose([(6, 0), (7, 0), (8, 0), (9, 0)], row, col)]
            screen.blit(sprite, (x, y))

    # Faint engraved sigil in the central room, drawn on top of the genuine
    # floor tiles but behind all actual objects and the original robot.
    sr, sc = level["start"]
    cx, cy = grid_to_pixel(sr, sc)
    center = (cx + CELL_SIZE // 2, cy + CELL_SIZE // 2)
    motif = pygame.Surface((CELL_SIZE * 7, CELL_SIZE * 7), pygame.SRCALPHA)
    mc = (motif.get_width() // 2, motif.get_height() // 2)
    for radius, opacity in ((76, 30), (57, 42), (34, 37)):
        pygame.draw.lines(motif, (202, 125, 184, opacity), True,
                          [(mc[0], mc[1] - radius), (mc[0] + radius, mc[1]),
                           (mc[0], mc[1] + radius), (mc[0] - radius, mc[1])], 2)
    screen.blit(motif, (center[0] - mc[0], center[1] - mc[1]))


def _draw_water(screen, sprites, level, tick_ms):
    """Visible turquoise water and a connected, walkable stone crossing.

    Exact water and stone coordinates come from levels.py. Collision and
    A* passability are unchanged by this drawing function.
    """
    blue = sprites["tile"][(7, 2)].copy()
    blue.fill((20, 112, 128, 0), special_flags=pygame.BLEND_RGBA_ADD)
    for row, col in level.get("water_tiles", ()):
        x, y = grid_to_pixel(row, col)
        screen.blit(blue, (x, y))
        wave = (tick_ms // 180 + col * 7 + row * 11) % CELL_SIZE
        pygame.draw.line(screen, (56, 165, 188),
                         (x + 5, y + 7 + wave // 5),
                         (x + CELL_SIZE - 6, y + 7 + wave // 5), 2)
        if (col + row + tick_ms // 430) % 3 == 0:
            pygame.draw.line(screen, (113, 205, 205),
                             (x + 9, y + 19), (x + 18, y + 19), 1)

    for pos in level.get("stepping_stones", ()):
        x, y = grid_to_pixel(*pos)
        # Each bridge piece uses the asset pack's masonry tile. It is safe to
        # traverse only because the same cell is clear in WorldState's grid.
        pygame.draw.rect(screen, (68, 134, 139),
                         (x + 1, y + 2, CELL_SIZE - 2, CELL_SIZE - 4), border_radius=4)
        screen.blit(sprites["tile"][(9, 5)], (x, y))
        pygame.draw.rect(screen, (164, 161, 155), (x + 3, y + 4, CELL_SIZE - 6, CELL_SIZE - 8), 1)


def _draw_decorations(screen, sprites, level, tick_ms):
    """Render all decor fields defined in levels.py, with original coordinates."""
    tile = sprites["tile"]
    # Static, obstacle-sized props (not invented map cells).
    mapping = {
        "barrels": (4, 8), "bookcases": (3, 8), "tables": (0, 8),
        "bones": (8, 7), "cobwebs": (4, 6), "clay_pots": (5, 8),
        "desk_scrolls": (1, 8), "open_books": (2, 8),
        "skeletons": (7, 7), "pickaxes": (8, 6),
        "ladders": (6, 4), "rocks": (9, 5), "small_chests": (2, 8),
        "fountains": (7, 8), "skulls": (7, 7),
        "center_statues": (9, 4), "treasure_statues": (9, 4),
    }
    for field, tile_coord in mapping.items():
        _draw_field(screen, level, field, tile[tile_coord])

    for position in level.get("crates", ()):
        _draw_image(screen, _anim(sprites["crates"], tick_ms, 400), position)
    for position in level.get("chests", ()):
        _draw_image(screen, _anim(sprites["chest"], tick_ms, 450), position)
    for position in level.get("chest_stacks", ()):
        _draw_image(screen, _anim(sprites["small_crates"], tick_ms, 500), position)
    for position in level.get("gold_chests", ()):
        _draw_image(screen, _anim(sprites["chest"], tick_ms, 350), position)
    for position in level.get("potions", ()):
        _draw_image(screen, _anim(sprites["potions"], tick_ms), position)
    for position in level.get("banners", ()):
        _draw_image(screen, _anim(sprites["flag"], tick_ms), position)
    for position in level.get("crystals", ()):
        _draw_image(screen, tile[(7, 8)], position)
    for position in level.get("desk_candles", ()):
        _draw_image(screen, _anim(sprites["candles"], tick_ms), position)

    for position in level.get("torches", ()):
        _draw_image(screen, _anim(sprites["torches"], tick_ms, 170), position)



def _draw_csp_chamber(screen, sprites, level, state, tick_ms,
                      puzzle_result=None, puzzle_started_at=None):
    """Present Member C's five switches clearly in a spacious 3 + 2 layout.

    Visual placement is deliberately separate from logical tile positions:
    state, A* paths, puzzle rules and switch assignments are never modified.
    """
    puzzle_row, puzzle_col = level["puzzle"]
    solved = bool(state is not None and state.puzzle_solved)
    settings = getattr(puzzle_result, "settings", None) or {}
    applying = puzzle_started_at is not None and bool(settings)
    elapsed = max(0, tick_ms - puzzle_started_at) if applying else 0
    shown = min(5, 1 + elapsed // 240) if applying else (5 if solved else 0)

    palette = {
        "RED": (232, 91, 88),
        "BLUE": (72, 164, 246),
        "GREEN": (87, 222, 139),
        "YELLOW": (245, 204, 91),
        "WHITE": (231, 233, 239),
    }
    order = ("RED", "BLUE", "GREEN", "YELLOW", "WHITE")
    # Only draw switches that Member D's level actually defines.
    authored_switches = {
        name for _, name in level.get("pressure_plates", ()) if name in palette
    }

    # Generous, centered 3-on-top / 2-on-bottom spacing. Grid coordinates are
    # for DRAWING ONLY and are anchored to the original puzzle location.
    visual_slots = {
        "RED": (puzzle_row - 2, puzzle_col - 5),
        "BLUE": (puzzle_row - 2, puzzle_col - 1),
        "GREEN": (puzzle_row - 2, puzzle_col + 3),
        "YELLOW": (puzzle_row, puzzle_col - 3),
        "WHITE": (puzzle_row, puzzle_col + 2),
    }

    name_font = pygame.font.Font(None, 21)
    status_font = pygame.font.Font(None, 23)
    header_font = pygame.font.Font(None, 21)

    # Header is above the switches rather than overlapping any of them.
    heading_x, heading_y = grid_to_pixel(puzzle_row - 3, puzzle_col - 4)
    header = header_font.render("CSP  /  5 SWITCHES", True, (230, 205, 242))
    screen.blit(header, (heading_x, heading_y + 7))

    phase = "SOLVED" if solved else "SOLVING" if applying else "PENDING"
    phase_color = ((112, 248, 173) if solved else
                   (223, 180, 248) if applying else (190, 176, 209))
    phase_image = header_font.render(phase, True, phase_color)
    phase_x, _ = grid_to_pixel(puzzle_row - 3, puzzle_col + 4)
    screen.blit(phase_image, (phase_x, heading_y + 7))

    card_width = 76
    card_height = 58

    for index, name in enumerate(order):
        if name not in authored_switches:
            continue

        row, col = visual_slots[name]
        tile_x, tile_y = grid_to_pixel(row, col)
        center_x = tile_x + CELL_SIZE // 2
        x = center_x - card_width // 2
        y = tile_y

        applied = (solved or applying) and index < shown
        on = bool(settings.get(name, False)) if applied else False

        card = pygame.Rect(x, y, card_width, card_height)
        pygame.draw.rect(screen, (23, 19, 36), card, border_radius=6)
        border = ((80, 207, 132) if applied and on else
                  (110, 114, 134) if applied else (108, 82, 133))
        pygame.draw.rect(screen, border, card, width=2, border_radius=6)

        # Color dot always identifies the switch; it does NOT imply ON.
        pygame.draw.circle(screen, palette[name], (x + 13, y + 17), 6)
        label = name_font.render(name, True, (242, 237, 243))
        screen.blit(label, (x + 24, y + 10))

        # A separate, high-contrast status pill makes the solved combination
        # unambiguous: vivid green ON, neutral gray OFF, purple '?' pending.
        if not applied:
            status = "?"
            fill = (51, 38, 68)
            ink = (220, 187, 245)
        elif on:
            status = "ON"
            fill = (32, 94, 67)
            ink = (170, 255, 199)
        else:
            status = "OFF"
            fill = (66, 66, 79)
            ink = (235, 235, 241)

        pill = pygame.Rect(x + 7, y + 31, card_width - 14, 22)
        pygame.draw.rect(screen, fill, pill, border_radius=4)
        status_surface = status_font.render(status, True, ink)
        screen.blit(status_surface,
                    (pill.centerx - status_surface.get_width() // 2,
                     pill.centery - status_surface.get_height() // 2))


def _draw_objectives(screen, sprites, level, state, tick_ms):
    tile = sprites["tile"]
    # State-aware sprites: remove key after pickup, indicate unlocked door,
    # and distinguish an opened exit. No interaction rules are changed.
    def highlight(position, color):
        x, y = grid_to_pixel(*position)
        pulse = (tick_ms // 260) % 3
        pygame.draw.rect(screen, color, (x + 1 - pulse, y + 1 - pulse,
                         CELL_SIZE - 2 + 2 * pulse, CELL_SIZE - 2 + 2 * pulse), 2)

    if not (state is not None and state.has_key):
        highlight(level["key"], (236, 194, 83))
        _draw_image(screen, _anim(sprites["key"], tick_ms, 160), level["key"])
    dr, dc = level["door"]
    dx, dy = grid_to_pixel(dr, dc)
    door_open = bool(state is not None and state.door_unlocked)
    if door_open:
        # Door leaf has *disappeared*. The AI walks through a visibly OPEN arch.
        screen.blit(tile[(7, 1)], (dx, dy))
        pygame.draw.rect(screen, (51, 184, 150), (dx + 2, dy + 2, 28, 28), 2)
        pygame.draw.line(screen, (105, 255, 201), (dx + 6, dy + 7),
                         (dx + 6, dy + 26), 3)
        pygame.draw.line(screen, (105, 255, 201), (dx + 26, dy + 7),
                         (dx + 26, dy + 26), 3)
    else:
        _draw_image(screen, tile[(8, 3)], level["door"])
    door_label = pygame.font.Font(None, 19).render(
        "OPEN" if door_open else "LOCKED", True,
        (90, 240, 171) if door_open else (250, 198, 103))
    screen.blit(door_label, (dx + 16 - door_label.get_width() // 2, dy - 17))
    exit_sprite = tile[(7, 3)] if state is not None and state.exit_open else tile[(8, 3)]
    highlight(level["exit"], (88, 211, 159))
    highlight(level["exit"], (247, 210, 140))
    _draw_image(screen, exit_sprite, level["exit"])


def draw_level(screen, sprites, level_id, state=None, tick_ms=None,
               puzzle_result=None, puzzle_started_at=None):
    """Paint the real 47x25 dungeon from level data, never a reference image.

    Includes all spike_traps, water_tiles, stepping_stones, pressure_plates,
    permanent props, animated torches, key, door, puzzle and exit.
    """
    from game import obstacles

    level = get_level(level_id)
    now = pygame.time.get_ticks() if tick_ms is None else tick_ms
    screen.fill((18, 13, 26))
    _draw_background(screen, sprites, level)
    _draw_water(screen, sprites, level, now)
    _draw_decorations(screen, sprites, level, now)
    # Animated trap imagery remains tied to Member A's existing spike clock.
    spike_image = sprites["spikes"][obstacles.get_spike_frame()]
    for position in level.get("spike_traps", ()):
        _draw_image(screen, spike_image, position)
    if state is not None:
        # Dynamic blockers are visibly represented without changing state.
        for position in state.dynamic_obstacles:
            _draw_image(screen, sprites["tile"][(3, 8)], position)
    _draw_objectives(screen, sprites, level, state, now)
    _draw_csp_chamber(screen, sprites, level, state, now,
                      puzzle_result, puzzle_started_at)


def draw_robot(screen, sprites, robot, tick_ms=None):
    """Draw smooth pixel-position robot controlled by the existing movement."""
    action = "walk" if robot.is_moving else "idle"
    animation = sprites["robot"][(action, robot.direction)]
    now = pygame.time.get_ticks() if tick_ms is None else tick_ms
    index = robot.frame_index % len(animation)
    # Pixel-perfect 32x32 sprite aligned to Member D's grid.
    # A subtle floor marker helps the small robot stand out from purple tiles.
    center = (round(robot.robot_x + CELL_SIZE / 2),
              round(robot.robot_y + CELL_SIZE - 3))
    pygame.draw.ellipse(screen, (43, 122, 129),
                        (center[0] - 13, center[1] - 5, 26, 11), 2)
    # Enlarge the art ONLY. Physical cell size / AI coordinates stay 32x32.
    robot_size = round(CELL_SIZE * 1.58)
    sprite = pygame.transform.scale(animation[index], (robot_size, robot_size))
    dx = (robot_size - CELL_SIZE) // 2
    dy = robot_size - CELL_SIZE
    screen.blit(sprite, (round(robot.robot_x) - dx,
                         round(robot.robot_y) - dy))


def draw_hud(screen, state, decision=None, search_stats=None, puzzle_result=None):
    """Compact read-only game HUD; Member E can later replace it."""
    font = pygame.font.Font(None, 26)
    small = pygame.font.Font(None, 21)
    label = get_level(state.level_id)["name"]
    goal = decision.get("goal", "INITIALIZING") if decision else "PREVIEW"
    step = f"Key: {'YES' if state.has_key else 'NO'}   Door: {'OPEN' if state.door_unlocked else 'LOCKED'}   Puzzle: {'SOLVED' if state.puzzle_solved else 'PENDING'}"
    screen.blit(font.render("ROGUEMIND", True, (247, 210, 140)), (MARGIN_X, 10))
    screen.blit(small.render(label, True, (187, 179, 198)), (MARGIN_X + 175, 15))
    screen.blit(small.render(f"AI GOAL: {goal}", True, (116, 225, 190)),
                (WINDOW_WIDTH - 400, 15))
    screen.blit(small.render(step, True, (207, 197, 214)), (MARGIN_X, WINDOW_HEIGHT - 39))
    if puzzle_result is not None and puzzle_result.settings:
        values = "  ".join(f"{name[0]}:{'ON' if val else 'OFF'}"
                           for name, val in puzzle_result.settings.items())
        label_text = "CSP SWITCHES  " + values
        label_surface = small.render(label_text, True, (116, 225, 190))
        screen.blit(label_surface, (MARGIN_X + 400, WINDOW_HEIGHT - 22))
    if search_stats:
        screen.blit(small.render(
            f"A*: {search_stats.get('path_length', 0)} steps / "
            f"{search_stats.get('nodes_explored', 0)} nodes",
            True, (184, 173, 208)), (WINDOW_WIDTH - 370, WINDOW_HEIGHT - 39))


def main():
    """Standalone animated visual preview (gameplay runs through main.py)."""
    pygame.init()
    info = pygame.display.Info()
    monitor_w = info.current_w if info.current_w > 0 else 1280
    monitor_h = info.current_h if info.current_h > 0 else 800
    scale = min(1.0, max(640, monitor_w - 100) / WINDOW_WIDTH,
                max(400, monitor_h - 120) / WINDOW_HEIGHT)
    view_size = (max(1, int(WINDOW_WIDTH * scale)),
                 max(1, int(WINDOW_HEIGHT * scale)))
    screen = pygame.display.set_mode(view_size)
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)).convert()
    pygame.display.set_caption("RogueMind — asset-based dungeon preview")
    from game.state import WorldState
    from game import obstacles

    state = WorldState("ember_crypt")
    sprites = load_sprites()
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        obstacles.update_spikes()
        draw_level(canvas, sprites, state.level_id, state)
        draw_hud(canvas, state)
        if screen.get_size() == canvas.get_size():
            screen.blit(canvas, (0, 0))
        else:
            pygame.transform.scale(canvas, screen.get_size(), screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
