
import pytest

from ai.agent_controller import AgentController
from ai.behavior_tree import Status
from game.state import WorldState


class FakeMovement:
    """Simulate whether the robot's next spike crossing is unsafe."""

    def __init__(self):
        self.spikes_blocking = False

    def is_next_crossing_blocked(self):
        return self.spikes_blocking


@pytest.fixture
def setup_agent():
    """Create a fresh game state and controller for each test."""
    state = WorldState("ember_crypt")
    movement = FakeMovement()
    agent = AgentController(state, movement)

    return state, movement, agent


def check_scenario(agent, expected_goal, expected_status):
    result = agent.update()

    print(f"\nExpected goal: {expected_goal}")
    print(f"Actual goal:   {result['goal']}")
    print(f"Status:        {result['status'].name}")
    print(f"Reason:        {result['reason']}")

    assert result["goal"] == expected_goal
    assert result["status"] == expected_status


# Scenario 1: Robot needs a key
def test_find_key(setup_agent):
    state, movement, agent = setup_agent

    state.has_key = False

    check_scenario(agent, "FIND_KEY", Status.SUCCESS)


# Scenario 2: Robot has key but door is locked
def test_unlock_door(setup_agent):
    state, movement, agent = setup_agent

    state.has_key = True
    state.door_unlocked = False

    check_scenario(agent, "UNLOCK_DOOR", Status.SUCCESS)


# Scenario 3: Door unlocked but puzzle is unsolved
def test_solve_puzzle(setup_agent):
    state, movement, agent = setup_agent

    state.has_key = True
    state.door_unlocked = True
    state.puzzle_solved = False

    check_scenario(agent, "SOLVE_PUZZLE", Status.SUCCESS)


# Scenario 4: Spikes block the robot's route
def test_wait_for_spikes(setup_agent):
    state, movement, agent = setup_agent

    movement.spikes_blocking = True

    check_scenario(agent, "WAIT_FOR_SPIKES", Status.RUNNING)


# Scenario 5: Puzzle solved and exit is open
def test_reach_exit(setup_agent):
    state, movement, agent = setup_agent

    state.has_key = True
    state.door_unlocked = True
    state.puzzle_solved = True
    state.level_complete = False

    check_scenario(agent, "REACH_EXIT", Status.SUCCESS)


# Scenario 6: Robot completes the level
def test_level_complete(setup_agent):
    state, movement, agent = setup_agent

    state.level_complete = True

    check_scenario(agent, "LEVEL_COMPLETE", Status.SUCCESS)


# Scenario 7: Test the fallback action directly
def test_no_available_goal(setup_agent):
    state, movement, agent = setup_agent

    result = agent.no_available_goal()

    assert result == Status.FAILURE
    assert agent.current_goal == "NO_AVAILABLE_GOAL"
