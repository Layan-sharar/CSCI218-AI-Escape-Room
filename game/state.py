from game.levels import get_grid, get_level


class WorldState:
    """Track the player's progress through one level."""

    def __init__(self, level_id):
        self.level_id = level_id
        level = get_level(level_id)

        self.start_position = level["start"]
        self.key_position = level["key"]
        self.door_position = level["door"]
        self.puzzle_position = level["puzzle"]
        self.exit_position = level["exit"]

        self.reset()

    def reset(self):
        """Return the player and level progress to the starting state."""
        self.player_position = self.start_position
        self.has_key = False
        self.door_unlocked = False
        self.puzzle_solved = False
        self.level_complete = False

    @property
    def exit_open(self):
        """The exit opens after the door is unlocked and puzzle is solved."""
        return self.door_unlocked and self.puzzle_solved

    def get_ai_grid(self):
        """Give the AI a grid where walls and a locked door are blocked."""
        grid = get_grid(self.level_id)

        if not self.door_unlocked:
            row, column = self.door_position
            grid[row][column] = 1

        return grid
    