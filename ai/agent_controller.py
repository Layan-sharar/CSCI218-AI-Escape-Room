"""Autonomous Behavior Tree goal selection for RogueMind's WorldState.

The controller chooses goals; main.py executes navigation and interactions.
No manual controls are needed.
"""
from ai.behavior_tree import Status, Selector, Sequence, Condition, Action
from ai.navigation import find_path


class AgentController:
    def __init__(self, world_state, movement=None):
        self.game_state = world_state
        self.movement = movement
        self.current_goal = None
        self.target_position = None
        self.reason = ""
        self.tree = self.build_tree()

    def set_goal(self, goal, position, reason):
        self.current_goal = goal
        self.target_position = position
        self.reason = reason
        return Status.SUCCESS

    def _spikes_blocking(self):
        return bool(self.movement and self.movement.is_next_crossing_blocked())

    def _choose_door_approach(self):
        """Find a reachable tile beside the locked door, not the blocked door itself."""
        state = self.game_state
        dr, dc = state.door_position
        grid = state.get_ai_grid()
        neighbours = [(dr - 1, dc), (dr + 1, dc), (dr, dc - 1), (dr, dc + 1)]
        reachable = []
        for row, col in neighbours:
            if not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
                continue
            if grid[row][col] != 0:
                continue
            result = find_path(grid, state.player_position, (row, col))
            if result["found"]:
                reachable.append((result["cost"], (row, col)))
        if not reachable:
            self.current_goal = "NO_AVAILABLE_GOAL"
            self.target_position = None
            self.reason = "No reachable tile beside the locked door"
            return Status.FAILURE
        reachable.sort()
        return self.set_goal("UNLOCK_DOOR", reachable[0][1], "Approach the door to unlock it")

    def build_tree(self):
        return Selector([
            Sequence([
                Condition(lambda: self.game_state.level_complete, "Level Completed"),
                Action(self.finish_level, "Finish Level"),
            ], "Check Completion"),
            Sequence([
                Condition(self._spikes_blocking, "Spikes Blocking Route"),
                Action(self.wait_for_spikes, "Wait for Spikes"),
            ], "Handle Spikes"),
            Sequence([
                Condition(lambda: not self.game_state.has_key, "Key Missing"),
                Action(lambda: self.set_goal("FIND_KEY", self.game_state.key_position,
                                             "The robot needs the key"), "Choose Key"),
            ], "Find Key"),
            Sequence([
                Condition(lambda: not self.game_state.door_unlocked, "Door Locked"),
                Action(self._choose_door_approach, "Choose Door Approach"),
            ], "Unlock Door"),
            Sequence([
                Condition(lambda: not self.game_state.puzzle_solved, "Puzzle Unsolved"),
                Action(lambda: self.set_goal("SOLVE_PUZZLE", self.game_state.puzzle_position,
                                             "The puzzle must be solved"), "Choose Puzzle"),
            ], "Solve Puzzle"),
            Sequence([
                Condition(lambda: self.game_state.exit_open, "Exit Open"),
                Action(lambda: self.set_goal("REACH_EXIT", self.game_state.exit_position,
                                             "The exit is accessible"), "Choose Exit"),
            ], "Reach Exit"),
        ], "Choose Goal")

    def update(self):
        self.current_goal = None
        self.target_position = None
        self.reason = ""
        status = self.tree.tick()
        if status == Status.FAILURE and self.current_goal is None:
            self.no_available_goal()
        return {"status": status, "goal": self.current_goal,
                "target": self.target_position, "reason": self.reason}

    def wait_for_spikes(self):
        self.current_goal = "WAIT_FOR_SPIKES"
        self.target_position = None
        self.reason = "Waiting for a safe spike crossing"
        return Status.RUNNING

    def finish_level(self):
        return self.set_goal("LEVEL_COMPLETE", None, "The robot has successfully escaped")

    def no_available_goal(self):
        self.current_goal = "NO_AVAILABLE_GOAL"
        self.target_position = None
        self.reason = "No accessible objective is currently available"
        return Status.FAILURE
