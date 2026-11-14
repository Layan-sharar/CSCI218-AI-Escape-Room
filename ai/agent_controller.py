
from ai.behavior_tree import (
    Status,
    Selector,
    Sequence,
    Condition,
    Action
)


class AgentController:
    def __init__(self, game_state):
        self.game_state = game_state

        # The robot's current decision
        self.current_goal = None
        self.target_position = None
        self.reason = ""

        # Build the Behavior Tree
        self.tree = self.build_tree()

    def set_goal(self, goal, position, reason):
        self.current_goal = goal
        self.target_position = position
        self.reason = reason

        return Status.SUCCESS

    def build_tree(self):
        return Selector([

            Sequence([
                Condition(
                    lambda: self.game_state.get("level_complete", False),
                    "Level Completed"
                ),
                Action(
                    self.finish_level,
                    "Finish Level"
                )
            ], "Check Completion"),

            Sequence([
                Condition(
                    lambda: self.game_state["spikes_blocking"],
                    "Spikes Blocking Route"
                ),
                Action(
                    self.wait_for_spikes,
                    "Wait for Spikes"
                )
            ], "Handle Spikes"),
                        

            # Priority 1: Find the key
            Sequence([
                Condition(
                    lambda: not self.game_state["has_key"],
                    "Key Missing"
                ),
                Action(
                    lambda: self.set_goal(
                        "FIND_KEY",
                        self.game_state["key_position"],
                        "The robot needs the key"
                    ),
                    "Choose Key"
                )
            ], "Find Key"),

            # Priority 2: Solve the puzzle
            Sequence([
                Condition(
                    lambda: not self.game_state["puzzle_solved"],
                    "Puzzle Unsolved"
                ),
                Action(
                    lambda: self.set_goal(
                        "SOLVE_PUZZLE",
                        self.game_state["puzzle_position"],
                        "The puzzle must be solved"
                    ),
                    "Choose Puzzle"
                )
            ], "Solve Puzzle"),

            # Priority 3: Reach the exit
            Sequence([
                Condition(
                    lambda: self.game_state["exit_open"],
                    "Exit Open"
                ),
                Action(
                    lambda: self.set_goal(
                        "REACH_EXIT",
                        self.game_state["exit_position"],
                        "The exit is accessible"
                    ),
                    "Choose Exit"
                )
            ], "Reach Exit")

        ], "Choose Goal")

    def update(self):
        self.current_goal = None
        self.target_position = None
        self.reason = ""

        status = self.tree.tick()

        if status == Status.FAILURE:
            self.no_available_goal()

        return {
            "status": status,
            "goal": self.current_goal,
            "target": self.target_position,
            "reason": self.reason
        }

    def wait_for_spikes(self):
        self.current_goal = "WAIT_FOR_SPIKES"
        self.target_position = None
        self.reason = "Waiting for a safe spike crossing"
        
        return Status.RUNNING

    def finish_level(self):
        self.current_goal = "LEVEL_COMPLETE"
        self.target_position = None
        self.reason = "The robot has successfully escaped"

        return Status.SUCCESS
    
    def no_available_goal(self):
        self.current_goal = "NO_AVAILABLE_GOAL"
        self.target_position = None
        self.reason = "No accessible objective is currently available"

        return Status.FAILURE
