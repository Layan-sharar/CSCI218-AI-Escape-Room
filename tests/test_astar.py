import pytest

from ai.astar import astar_search, manhattan_distance
from ai.navigation import find_path, find_new_path


def make_open_grid(rows=10, cols=10):
    return [[0 for col in range(cols)] for row in range(rows)]


def is_valid_path(grid, path, blocked_cells=None):
    if path is None or len(path) == 0:
        return False

    blocked_cells = set(blocked_cells or [])

    for row, col in path:
        if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
            return False
        if grid[row][col] != 0 or (row, col) in blocked_cells:
            return False

    for current, next_position in zip(path, path[1:]):
        distance = (
            abs(current[0] - next_position[0])
            + abs(current[1] - next_position[1])
        )
        if distance != 1:
            return False

    return True


def test_finds_path_on_open_grid():
    grid = make_open_grid()
    result = find_path(grid, (0, 0), (9, 9))

    assert result["found"] is True
    assert result["path"][0] == (0, 0)
    assert result["path"][-1] == (9, 9)
    assert is_valid_path(grid, result["path"])
    assert result["cost"] == 18
    assert result["path_length"] == 18


def test_finds_route_around_walls():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    result = astar_search(grid, (0, 0), (4, 4))

    assert result["found"] is True
    assert is_valid_path(grid, result["path"])
    assert result["cost"] == result["path_length"]


def test_returns_no_path_when_goal_is_enclosed():
    grid = [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ]

    result = find_path(grid, (0, 0), (1, 1))

    assert result["found"] is False
    assert result["path"] is None
    assert result["cost"] is None


def test_returns_no_path_when_start_or_goal_is_blocked():
    grid = make_open_grid(3, 3)
    grid[0][0] = 1

    result = find_path(grid, (0, 0), (2, 2))
    assert result["found"] is False
    assert result["path"] is None

    grid[0][0] = 0
    grid[2][2] = 1

    result = find_path(grid, (0, 0), (2, 2))
    assert result["found"] is False


def test_returns_no_path_for_out_of_bounds_position():
    grid = make_open_grid(3, 3)

    result = find_path(grid, (-1, 0), (2, 2))
    assert result["found"] is False

    result = find_path(grid, (0, 0), (3, 3))
    assert result["found"] is False


def test_zero_heuristic_finds_same_optimal_cost():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    astar_result = find_path(
        grid, (0, 0), (4, 4), use_heuristic=True
    )
    uniform_result = find_path(
        grid, (0, 0), (4, 4), use_heuristic=False
    )

    assert astar_result["found"] is True
    assert uniform_result["found"] is True
    assert astar_result["cost"] == uniform_result["cost"]


def test_extra_blocked_cells_are_avoided():
    grid = make_open_grid(5, 5)
    extra_blocked = {(0, 1), (1, 1), (2, 1), (3, 1)}

    result = find_path(
        grid,
        (0, 0),
        (0, 4),
        blocked_cells=extra_blocked
    )

    assert result["found"] is True
    assert is_valid_path(grid, result["path"], extra_blocked)
    assert result["cost"] > 4


def test_replans_when_old_route_is_blocked():
    grid = make_open_grid(5, 5)

    first_result = find_path(grid, (2, 0), (2, 4))
    old_path = first_result["path"]

    # Block a tile on the original route, then search using the updated map.
    newly_blocked = {old_path[2]}
    second_result = find_new_path(
        grid,
        (2, 0),
        (2, 4),
        blocked_cells=newly_blocked
    )

    assert first_result["found"] is True
    assert second_result["found"] is True
    assert is_valid_path(grid, second_result["path"], newly_blocked)
    assert second_result["path"] != old_path


def test_replanning_reports_unreachable_goal():
    grid = make_open_grid(3, 3)
    newly_blocked = {
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
    }

    result = find_new_path(
        grid,
        (0, 0),
        (2, 2),
        blocked_cells=newly_blocked
    )

    assert result["found"] is False
    assert result["path"] is None


def test_start_equals_goal():
    grid = make_open_grid(3, 3)

    result = find_path(grid, (1, 1), (1, 1))

    assert result["found"] is True
    assert result["path"] == [(1, 1)]
    assert result["cost"] == 0
    assert result["path_length"] == 0


def test_search_statistics_are_returned():
    grid = make_open_grid(4, 4)
    result = find_path(grid, (0, 0), (3, 3))

    assert isinstance(result["nodes_explored"], int)
    assert result["nodes_explored"] > 0
    assert isinstance(result["runtime"], float)
    assert result["runtime"] >= 0


def test_rejects_non_rectangular_grid():
    grid = [
        [0, 0, 0],
        [0, 0],
    ]

    with pytest.raises(ValueError):
        find_path(grid, (0, 0), (1, 1))


def test_manhattan_distance():
    assert manhattan_distance((1, 2), (4, 6)) == 7
