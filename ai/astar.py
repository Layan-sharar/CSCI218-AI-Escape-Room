"""A* pathfinding for the ROGUEMIND dungeon grid.

Grid convention:
    0 = walkable
    1 = blocked

Positions are always (row, column). Movement is limited to the four
orthogonal neighbours, and each move has a cost of 1.
"""

import heapq
import itertools
import time


def manhattan_distance(position, goal):
    """Estimate the distance between two grid positions."""
    return (
        abs(position[0] - goal[0])
        + abs(position[1] - goal[1])
    )


def _is_valid_position(grid, position):
    """Return True if position is inside the grid."""
    if not isinstance(position, (tuple, list)) or len(position) != 2:
        return False

    row, col = position

    if not isinstance(row, int) or not isinstance(col, int):
        return False

    return (
        0 <= row < len(grid)
        and 0 <= col < len(grid[0])
    )


def _make_result(path, cost, explored, runtime, found):
    """Build the standard result dictionary used by the project."""
    if path is None:
        path_length = 0
    else:
        path_length = max(0, len(path) - 1)

    return {
        "found": found,
        "path": path,
        "cost": cost,
        "path_length": path_length,
        "nodes_explored": explored,
        "runtime": runtime,
    }


def astar_search(grid, start, goal, blocked_cells=None,
                 use_heuristic=True):
    """Find a shortest route through a rectangular grid.

    Args:
        grid: A rectangular 2D list. 0 means walkable; non-zero means blocked.
        start: Starting (row, column).
        goal: Destination (row, column).
        blocked_cells: Optional extra iterable of blocked (row, column) cells.
            This is useful for temporary obstacles such as active spikes.
        use_heuristic: True uses Manhattan distance (A*). False uses zero
            heuristic, making this Uniform-Cost Search for unit-cost moves.

    Returns:
        A dictionary containing:
            found: Whether a route was found.
            path: List of (row, column) positions, including start and goal,
                  or None if no route exists.
            cost: Total movement cost, or None if no route exists.
            path_length: Number of moves in the route.
            nodes_explored: Number of unique positions expanded.
            runtime: Search time in seconds.
    """
    started_at = time.perf_counter()

    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty 2D list")

    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid must contain at least one column")

    column_count = len(grid[0])

    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != column_count:
            raise ValueError("grid must be rectangular")

    if not isinstance(use_heuristic, bool):
        raise ValueError("use_heuristic must be True or False")

    start = tuple(start) if isinstance(start, (list, tuple)) else start
    goal = tuple(goal) if isinstance(goal, (list, tuple)) else goal

    if not _is_valid_position(grid, start):
        runtime = time.perf_counter() - started_at
        return _make_result(None, None, 0, runtime, False)

    if not _is_valid_position(grid, goal):
        runtime = time.perf_counter() - started_at
        return _make_result(None, None, 0, runtime, False)

    extra_blocked = set()
    if blocked_cells is not None:
        extra_blocked = {tuple(cell) for cell in blocked_cells}

    def is_blocked(position):
        row, col = position
        return grid[row][col] != 0 or position in extra_blocked

    if is_blocked(start) or is_blocked(goal):
        runtime = time.perf_counter() - started_at
        return _make_result(None, None, 0, runtime, False)

    if start == goal:
        runtime = time.perf_counter() - started_at
        return _make_result([start], 0, 1, runtime, True)

    def heuristic(position):
        if use_heuristic:
            return manhattan_distance(position, goal)
        return 0

    # Heap entries are (estimated total cost, insertion order, position).
    # The insertion order makes tie-breaking deterministic.
    counter = itertools.count()
    open_set = []
    heapq.heappush(
        open_set,
        (heuristic(start), next(counter), start)
    )

    came_from = {}
    g_score = {start: 0}
    closed_set = set()

    while open_set:
        current_f, order, current = heapq.heappop(open_set)

        if current in closed_set:
            continue

        closed_set.add(current)

        if current == goal:
            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            path.reverse()
            runtime = time.perf_counter() - started_at

            return _make_result(
                path,
                g_score[goal],
                len(closed_set),
                runtime,
                True
            )

        row, col = current
        neighbours = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]

        for neighbour in neighbours:
            if not _is_valid_position(grid, neighbour):
                continue

            if is_blocked(neighbour) or neighbour in closed_set:
                continue

            tentative_g = g_score[current] + 1

            if tentative_g < g_score.get(neighbour, float("inf")):
                came_from[neighbour] = current
                g_score[neighbour] = tentative_g
                estimated_total = tentative_g + heuristic(neighbour)

                heapq.heappush(
                    open_set,
                    (estimated_total, next(counter), neighbour)
                )

    runtime = time.perf_counter() - started_at
    return _make_result(None, None, len(closed_set), runtime, False)


# A short alias for code that prefers the name "find_path".
def find_path(grid, start, goal, blocked_cells=None,
              use_heuristic=True):
    """Compatibility wrapper around astar_search."""
    return astar_search(
        grid,
        start,
        goal,
        blocked_cells=blocked_cells,
        use_heuristic=use_heuristic
    )
