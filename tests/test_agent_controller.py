
from ai.agent_controller import AgentController
from ai.behavior_tree import Status

# Temporary game state for testing
game_state = {
    "has_key": False,
    "puzzle_solved": False,
    "exit_open": False,
    "level_complete": False,
    "spikes_blocking": False,
    "key_position": (2, 4),
    "puzzle_position": (5, 6),
    "exit_position": (7, 8)
}

agent = AgentController(game_state)


def check_scenario(number, expected_goal, expected_status):
    result = agent.update()

    print(f"\nScenario {number}")
    print(f"Expected goal: {expected_goal}")
    print(f"Actual goal:   {result['goal']}")
    print(f"Status:        {result['status'].name}")
    print(f"Reason:        {result['reason']}")

    assert result["goal"] == expected_goal
    assert result["status"] == expected_status

    print("PASSED")


# Scenario 1: Robot needs a key
check_scenario(1, "FIND_KEY", Status.SUCCESS)

# Scenario 2: Robot has key, but puzzle is unsolved
game_state["has_key"] = True
check_scenario(2, "SOLVE_PUZZLE", Status.SUCCESS)

# Scenario 3: Puzzle solved and exit is open
game_state["puzzle_solved"] = True
game_state["exit_open"] = True
check_scenario(3, "REACH_EXIT", Status.SUCCESS)

# Scenario 4: Spikes block the robot's route
game_state["spikes_blocking"] = True
check_scenario(4, "WAIT_FOR_SPIKES", Status.RUNNING)

# Scenario 5: Robot completes the level
game_state["level_complete"] = True
check_scenario(5, "LEVEL_COMPLETE", Status.SUCCESS)

# Scenario 6: No valid objective is available
game_state["level_complete"] = False
game_state["spikes_blocking"] = False
game_state["exit_open"] = False
check_scenario(6, "NO_AVAILABLE_GOAL", Status.FAILURE)

print("\nAll 6 Behavior Tree scenarios passed!")
