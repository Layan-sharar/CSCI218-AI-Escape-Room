
import pytest

from game.state import WorldState
from game.movement import RobotMovement
from game.obstacles import set_dynamic_obstacle


@pytest.fixture
def setup_robot():
    state = WorldState("ember_crypt")
    robot = RobotMovement(state)
    return state, robot


def find_adjacent_cell(state):
    """Find a walkable cell next to the robot."""
    row, col = state.player_position
    grid = state.get_ai_grid()

    for nr, nc in [
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    ]:
        if (0 <= nr < len(grid)
                and 0 <= nc < len(grid[nr])
                and grid[nr][nc] == 0):
            return nr, nc

    pytest.fail("No adjacent walkable cell found")


def test_valid_route(setup_robot):
    state, robot = setup_robot

    next_cell = find_adjacent_cell(state)
    route = [state.player_position, next_cell]

    assert robot.set_route(route) is True
    assert robot.route == route


def test_empty_route(setup_robot):
    state, robot = setup_robot

    assert robot.set_route([]) is False


def test_non_adjacent_route(setup_robot):
    state, robot = setup_robot

    row, col = state.player_position
    invalid_route = [
        (row, col),
        (row, col + 3),
    ]

    assert robot.set_route(invalid_route) is False


def test_wrong_starting_position(setup_robot):
    state, robot = setup_robot

    next_cell = find_adjacent_cell(state)

    assert robot.set_route([next_cell]) is False


def test_blocked_route(setup_robot):
    state, robot = setup_robot

    next_cell = find_adjacent_cell(state)
    route = [state.player_position, next_cell]

    assert set_dynamic_obstacle(
        state, next_cell, blocked=True
    ) is True

    assert robot.set_route(route) is False


def test_new_obstacle_blocks_existing_route(setup_robot):
    state, robot = setup_robot

    next_cell = find_adjacent_cell(state)
    route = [state.player_position, next_cell]

    assert robot.set_route(route) is True

    assert set_dynamic_obstacle(
        state, next_cell, blocked=True
    ) is True

    # The movement system must reject the blocked step.
    assert robot.update(0.1) is False
    assert state.player_position == state.start_position
