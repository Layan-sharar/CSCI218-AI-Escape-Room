"""Full agent flow: world (D) -> Behaviour Tree (A) -> A* (B) -> movement (A) -> CSP (C) -> Inspector (E).

Drives main.update(dt) without a window. The spikes run on simulation time,
so every run here is deterministic.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest

import game.interactions as interactions
import game.movement as movement
import main
from ai.navigation import find_path

DT = 0.05
MAX_FRAMES = 20_000


def run_until(done, max_frames=MAX_FRAMES):
    for frame in range(max_frames):
        main.update(DT)
        if done():
            return frame
    pytest.fail(f"not done after {max_frames} frames; goal {main.run['goal']}")


def run_level(level_id):
    main.load(level_id)
    return run_until(lambda: main.world.level_complete)


def messages():
    return [event["message"] for event in main.inspector.events]


def optimal_steps(level_id):
    """Shortest key -> door -> puzzle -> exit trip, from the pathfinder alone."""
    main.load(level_id)
    world = main.world
    to_key = find_path(world.get_ai_grid(), world.start_position, world.key_position)
    world.door_unlocked = True
    grid = world.get_ai_grid()
    to_puzzle = find_path(grid, world.key_position, world.puzzle_position)
    to_exit = find_path(grid, world.puzzle_position, world.exit_position)
    return to_key["path_length"] + to_puzzle["path_length"] + to_exit["path_length"]


@pytest.mark.parametrize("level_id", ["ember_crypt", "lower_crypt"])
def test_agent_escapes_each_level_along_optimal_routes(level_id):
    expected = optimal_steps(level_id)
    run_level(level_id)
    world = main.world
    assert world.has_key and world.door_unlocked and world.puzzle_solved
    assert world.player_position == world.exit_position
    assert main.run["steps"] == expected


def test_inspector_saw_the_whole_run_in_order():
    main.inspector.events = type(main.inspector.events)(maxlen=100)
    run_level("ember_crypt")
    main.update(DT)  # the Behaviour Tree sees the finished level on the next frame
    log = messages()
    order = ["Goal: FIND_KEY", "Picked up the key", "Unlocked the door",
             "Puzzle solved", "Reached the exit", "Goal: LEVEL_COMPLETE"]
    positions = [next(i for i, m in enumerate(log) if m.startswith(o)) for o in order]
    assert positions == sorted(positions)
    assert any(m.startswith("Route to") for m in log)
    metrics = main.inspector.metrics
    assert metrics["goal"] == "LEVEL_COMPLETE"
    assert metrics["puzzle"] == "Solved"
    assert metrics["branch"] == ["Choose Goal", "Check Completion", "Finish Level"]


def test_robot_waits_for_spikes_and_never_stands_on_them_while_up():
    main.load("ember_crypt")
    waited = False
    for _ in range(MAX_FRAMES):
        main.update(DT)
        waited |= main.run["goal"] == "WAIT_FOR_SPIKES"
        robot = movement.robot_rect_at(movement.robot_x, movement.robot_y)
        if robot.colliderect(main.obstacles.get_spike_rect()):
            assert movement.crossing_spikes, "robot on the spikes without a safe crossing"
        if main.world.level_complete:
            break
    assert waited
    assert main.world.level_complete


def test_reset_restarts_the_same_run():
    run_level("ember_crypt")
    first = main.run["steps"]
    main.playback.reset()  # the Reset button
    assert main.world.player_position == main.world.start_position
    assert not main.world.has_key
    assert main.run["steps"] == 0
    assert not main.inspector.events
    run_until(lambda: main.world.level_complete)
    assert main.run["steps"] == first


def test_obstacle_on_the_route_forces_a_replan_around_it():
    # Only the last leg has loops (around the pool), so block a cell there
    main.load("ember_crypt")
    exit_position = main.world.exit_position
    run_until(lambda: main.plan["target"] == exit_position and main.plan["path"] is not None)
    route = main.plan["path"]

    # Block a cell ahead that still leaves another way to the exit
    blocked = None
    for cell in route[4:-1]:
        grid = main.planning_grid()
        grid[cell[0]][cell[1]] = 1
        if find_path(grid, main.world.player_position, exit_position)["found"]:
            blocked = cell
            break
    assert blocked, "no cell on this route has a detour"
    assert interactions.set_dynamic_obstacle(main.world, blocked)

    visited = set()
    def escaped():
        visited.add((movement.robot_row, movement.robot_col))
        return main.world.level_complete
    run_until(escaped)

    assert blocked not in visited
    assert any(m.startswith("Replanned around an obstacle") for m in messages())


def test_robot_stops_when_an_obstacle_seals_the_only_way():
    main.load("ember_crypt")
    run_until(lambda: main.plan["path"] is not None)
    key_row, key_col = main.world.key_position
    for cell in ((key_row - 1, key_col), (key_row + 1, key_col), (key_row, key_col - 1), (key_row, key_col + 1)):
        interactions.set_dynamic_obstacle(main.world, cell)

    for _ in range(2000):
        main.update(DT)
    assert not main.world.has_key
    assert not movement.is_moving
    assert any(m.startswith("No route to") for m in messages())
