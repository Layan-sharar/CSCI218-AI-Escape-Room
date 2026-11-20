

from html import escape
from pathlib import Path

from ai.navigation import find_path
from game.state import WorldState

LEVEL_ID = "ember_crypt"
NEW_OBSTACLE = (12, 22)


def valid_route(path, grid):
    """Verify every route cell is walkable and each step is orthogonal."""
    if not path:
        return False
    for row, col in path:
        if not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
            return False
        if grid[row][col] != 0:
            return False
    return all(
        abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
        for a, b in zip(path, path[1:])
    )


def svg_visualization(before_grid, after_grid, before, after, start, goal):
    """Make an evidence diagram directly from the actual dungeon and A* routes."""
    cell = 16
    rows, cols = len(before_grid), len(before_grid[0])
    map_width, map_height = cols * cell, rows * cell
    x_left, gap = 42, 68
    x_right = x_left + map_width + gap
    top = 181
    width, height = x_right + map_width + 42, 696
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#101521"/>',
        '<text x="42" y="48" fill="#f6f7fa" font-size="28" font-weight="bold" font-family="Arial, sans-serif">RogueMind — A* Dynamic Obstacle Replanning</text>',
        '<text x="42" y="78" fill="#abb6cb" font-size="17" font-family="Arial, sans-serif">Controlled test using the real Ember Crypt navigation grid and ai.navigation.find_path()</text>',
        f'<text x="42" y="105" fill="#f4b860" font-size="16" font-family="Arial, sans-serif">New obstacle at (row {NEW_OBSTACLE[0]}, column {NEW_OBSTACLE[1]}) on the original route</text>',
    ]

    for x, grid, result, heading, route_color, show_block in [
        (x_left, before_grid, before, "BEFORE  /  Original A* path", "#40d4ed", False),
        (x_right, after_grid, after, "AFTER  /  Recalculated A* path", "#70e4a5", True),
    ]:
        pieces.append(f'<rect x="{x-13}" y="122" width="{map_width+26}" height="515" rx="12" fill="#1b2434" stroke="#34445a" stroke-width="2"/>')
        pieces.append(f'<text x="{x}" y="155" fill="#f6f7fa" font-size="19" font-weight="bold" font-family="Arial, sans-serif">{escape(heading)}</text>')
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                fill = "#3b4454" if value == 0 else "#141b28"
                pieces.append(f'<rect x="{x+c*cell}" y="{top+r*cell}" width="{cell}" height="{cell}" fill="{fill}" stroke="#253043" stroke-width="0.65"/>')
        path = result["path"]
        if path:
            pts = " ".join(f"{x+c*cell+cell/2},{top+r*cell+cell/2}" for r, c in path)
            pieces.append(f'<polyline points="{pts}" fill="none" stroke="{route_color}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0.92"/>')
        r, c = NEW_OBSTACLE
        bx, by = x+c*cell, top+r*cell
        if show_block:
            pieces.append(f'<rect x="{bx+1}" y="{by+1}" width="{cell-2}" height="{cell-2}" rx="2" fill="#e65365"/>')
            pieces.append(f'<path d="M {bx+4} {by+4} L {bx+cell-4} {by+cell-4} M {bx+cell-4} {by+4} L {bx+4} {by+cell-4}" stroke="#fff" stroke-width="2"/>')
        else:
            pieces.append(f'<rect x="{bx+1}" y="{by+1}" width="{cell-2}" height="{cell-2}" fill="none" stroke="#f5b55e" stroke-width="2.5"/>')
        for (r, c), label, fill in ((start, "S", "#4f83ff"), (goal, "K", "#f4b860")):
            cx, cy = x+c*cell+cell/2, top+r*cell+cell/2
            pieces.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{fill}" stroke="#fff" stroke-width="1.4"/>')
            pieces.append(f'<text x="{cx}" y="{cy+3.5}" fill="#0c1522" font-size="11" text-anchor="middle" font-weight="bold" font-family="Arial, sans-serif">{label}</text>')
        first_step = result["path"][1]
        direction = "LEFT" if first_step == (start[0], start[1]-1) else "UP" if first_step == (start[0]-1, start[1]) else str(first_step)
        pieces.append(f'<text x="{x}" y="607" fill="{route_color}" font-size="16" font-weight="bold" font-family="Arial, sans-serif">{result["path_length"]} moves  ·  {result["nodes_explored"]} nodes explored  ·  first step: {escape(direction)}</text>')
    pieces += [
        '<text x="42" y="667" fill="#abb6cb" font-size="15" font-family="Arial, sans-serif">Legend: S = robot start  ·  K = key goal  ·  cyan/green = calculated route  ·  red X = newly blocked cell</text>',
        '</svg>',
    ]
    return "\n".join(pieces)


def main():
    state = WorldState(LEVEL_ID)
    start, goal = state.player_position, state.key_position
    before_grid = state.get_ai_grid()
    before = find_path(before_grid, start, goal)

    assert before["found"] and valid_route(before["path"], before_grid), "Original path invalid"
    assert NEW_OBSTACLE in before["path"][1:-1], "Chosen obstacle is not on the original route"
    assert before_grid[NEW_OBSTACLE[0]][NEW_OBSTACLE[1]] == 0, "Obstacle cell was already blocked"

    # Inject a temporary obstacle into the live WorldState grid representation.
    state.dynamic_obstacles.add(NEW_OBSTACLE)
    after_grid = state.get_ai_grid()
    after = find_path(after_grid, state.player_position, goal)

    assert after["found"] and valid_route(after["path"], after_grid), "Replanned path invalid"
    assert NEW_OBSTACLE not in after["path"], "Replanned route still crosses the blocked cell"
    assert before["path"][0] == after["path"][0] == start, "Routes do not share the starting cell"
    assert before["path"][-1] == after["path"][-1] == goal, "Routes do not reach the key"

    lines = [
        "=" * 62,
        "ROGUEMIND  |  A* DYNAMIC OBSTACLE REPLANNING TEST",
        "=" * 62,
        f"Level:                 {LEVEL_ID}",
        f"Start:                 {start}",
        f"Goal (key):            {goal}",
        f"New blocked cell:      {NEW_OBSTACLE}",
        "-" * 62,
        f"Original route found:  {before['found']}",
        f"Original path length:  {before['path_length']} moves",
        f"Original nodes:        {before['nodes_explored']}",
        f"Original first step:   {before['path'][1]}",
        "-" * 62,
        f"New route found:       {after['found']}",
        f"New path length:       {after['path_length']} moves",
        f"New nodes:             {after['nodes_explored']}",
        f"New first step:        {after['path'][1]}",
        f"Blocked cell avoided:  {NEW_OBSTACLE not in after['path']}",
        f"New route valid:       {valid_route(after['path'], after_grid)}",
        "-" * 62,
        "PASS: A* recalculated a valid route around the new obstacle.",
        "NOTE: Controlled pathfinding test; not a live gameplay capture.",
        "=" * 62,
    ]
    result_text = "\n".join(lines)
    print(result_text)
    output_dir = Path(__file__).resolve().parent
    (output_dir / "replanning_results.txt").write_text(result_text + "\n", encoding="utf-8")
    (output_dir / "replanning_comparison.svg").write_text(
        svg_visualization(before_grid, after_grid, before, after, start, goal),
        encoding="utf-8",
    )
    print("Saved: replanning_results.txt and replanning_comparison.svg")


if __name__ == "__main__":
    main()
