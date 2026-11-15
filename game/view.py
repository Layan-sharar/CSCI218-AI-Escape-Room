"""Fixed whole-dungeon presentation for RogueMind.

The complete eight-room map stays on screen; NO camera pans or follows the AI.
Only display formatting; WorldState/AI/navigation/robot physics are untouched.
"""

import pygame
from game import renderer
from game.levels import get_level

PALETTE = {
    "background": (14, 11, 23), "panel": (22, 17, 32),
    "edge": (87, 67, 98), "white": (245, 232, 221),
    "muted": (176, 166, 187), "gold": (245, 195, 106),
    "mint": (119, 227, 187), "blue": (109, 197, 216),
}
HEADER_H = 66
FOOTER_H = 79
PADDING = 12


def create_display():
    info = pygame.display.Info()
    max_w = info.current_w if info.current_w > 0 else 1600
    max_h = info.current_h if info.current_h > 0 else 960
    width = min(1620, max(760, max_w - 32))
    height = min(1000, max(550, max_h - 75))
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)


def _text(surface, string, pos, size, color, bold=False):
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return surface.blit(font.render(str(string), True, color), pos)


def present(screen, logical_screen, state, robot, decision, last_search,
            message, overview=False):
    """Show the entire level in a single stationary viewport.

    The robot position is used only by the renderer before this is called;
    there is deliberately no camera position or moving viewport.
    """
    width, height = screen.get_size()
    screen.fill(PALETTE["background"])
    pygame.draw.rect(screen, PALETTE["panel"], (0, 0, width, HEADER_H))
    pygame.draw.line(screen, PALETTE["edge"], (0, HEADER_H - 1), (width, HEADER_H - 1))

    _text(screen, "ROGUEMIND", (PADDING + 4, 13), 32, PALETTE["gold"], True)
    level_name = get_level(state.level_id)["name"]
    if width >= 1030:
        _text(screen, level_name, (240, 22), 22, PALETTE["muted"])
    goal = (decision or {}).get("goal") or "THINKING"
    goal_text = "AI: " + goal.replace("_", " ")
    estimated_width = len(goal_text) * 12
    _text(screen, goal_text, (max(242, width - estimated_width - 20), 21),
          23, PALETTE["mint"], True)

    # Full logical dungeon rectangle: no camera crop or player tracking.
    region = pygame.Rect(renderer.MARGIN_X, renderer.MAP_TOP,
                         renderer.MAP_WIDTH * renderer.CELL_SIZE,
                         renderer.MAP_HEIGHT * renderer.CELL_SIZE)
    available_width = max(1, width - PADDING * 2)
    available_height = max(1, height - HEADER_H - FOOTER_H - PADDING * 2)
    factor = min(available_width / region.width, available_height / region.height)
    size = (max(1, round(region.width * factor)),
            max(1, round(region.height * factor)))
    x = (width - size[0]) // 2
    y = HEADER_H + PADDING + (available_height - size[1]) // 2

    # Nearest-neighbour scaling keeps the actual asset pixels crisp.
    map_image = pygame.transform.scale(logical_screen.subsurface(region), size)
    screen.blit(map_image, (x, y))
    pygame.draw.rect(screen, PALETTE["edge"], (x - 1, y - 1, *size), 2)

    footer_y = height - FOOTER_H
    pygame.draw.rect(screen, PALETTE["panel"],
                     (0, footer_y, width, FOOTER_H))
    pygame.draw.line(screen, PALETTE["edge"], (0, footer_y), (width, footer_y))

    def status(label, ok):
        return f"{label}: {'DONE' if ok else 'PENDING'}"

    progress = (
        f"Key: {'YES' if state.has_key else 'NO'}   "
        f"Door: {'OPEN' if state.door_unlocked else 'LOCKED'}   "
        f"CSP: {'SOLVED' if state.puzzle_solved else 'PENDING'}   "
        f"Escape: {'COMPLETE' if state.level_complete else 'IN PROGRESS'}"
    )
    _text(screen, progress, (PADDING + 5, footer_y + 12),
          21 if width >= 1100 else 18, PALETTE["white"], True)
    _text(screen, str(message)[:95], (PADDING + 5, footer_y + 44),
          20, PALETTE["mint"])
    if last_search and width >= 970:
        stats = (f"A*: {last_search.get('path_length', 0)} moves, "
                 f"{last_search.get('nodes_explored', 0)} nodes")
        _text(screen, stats, (max(width - 293, 700), footer_y + 44),
              18, PALETTE["gold"])
    _text(screen, "R: reset", (max(6, width - 109), footer_y + 13),
          18, PALETTE["muted"])
