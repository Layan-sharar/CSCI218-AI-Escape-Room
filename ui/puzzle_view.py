"""Pygame window that shows the switch puzzle being solved.

How the game uses it:
    view = PuzzleView(puzzle, solve_puzzle(puzzle))
    view.apply_next()      # flips the next switch to the value the solver chose
    view.door_open         # True when all switches are set and the puzzle had a solution
    view.draw(surface)     # the surface should be SIZE

To try it alone: python -m ui.puzzle_view (SPACE next switch, R reset, I impossible puzzle, ESC quit).
"""

import pygame

from puzzles.switch_puzzle import default_puzzle, impossible_puzzle, solve_puzzle

SIZE = (640, 360)
WHITE, OFF_COLOUR = (240, 240, 240), (70, 70, 80)
COLOURS = {
    "RED": (214, 64, 64),
    "BLUE": (70, 120, 222),
    "GREEN": (82, 192, 102),
    "YELLOW": (240, 212, 72),
    "WHITE": (236, 236, 240),
}


class PuzzleView:
    def __init__(self, puzzle, result):
        pygame.font.init()
        self.font = pygame.font.Font(None, 22)
        self.puzzle = puzzle
        self.result = result
        self.reset()

    def reset(self):
        self.switch_states = {name: False for name in self.puzzle.switches}
        self.steps_applied = 0

    @property
    def door_open(self):
        return self.result.solved and self.steps_applied == len(self.puzzle.switches)

    def apply_next(self):
        if not self.result.solved or self.steps_applied >= len(self.puzzle.switches):
            return False
        name = self.puzzle.switches[self.steps_applied]
        self.switch_states[name] = self.result.settings[name]
        self.steps_applied += 1
        return True

    def draw(self, surface):
        def text(message, pos):
            surface.blit(self.font.render(message, True, WHITE), pos)

        surface.fill((30, 30, 40))
        text("Rules:", (20, 16))
        for i, rule in enumerate(self.puzzle.rules, start=1):
            text(f"{i}. {rule}", (20, 22 + i * 26))

        for i, name in enumerate(self.puzzle.switches):
            x = 20 + i * 110
            is_on = self.switch_states[name]
            pygame.draw.rect(surface, COLOURS[name] if is_on else OFF_COLOUR, (x, 240, 90, 40))
            text(f"{name} {'ON' if is_on else 'OFF'}", (x, 288))

        pygame.draw.rect(surface, (80, 190, 100) if self.door_open else (190, 70, 70), (480, 20, 120, 160))
        text("DOOR OPEN" if self.door_open else "DOOR SEALED", (490, 190))

        stats = self.result.stats
        if not self.result.solved:
            text("No solution: the door stays sealed", (20, 318))
        else:
            text(f"Applied {self.steps_applied}/{len(self.puzzle.switches)}", (20, 318))
        text(
            f"{self.result.strategy}: assignments {stats.assignments}, "
            f"backtracks {stats.backtracks}, {stats.runtime_seconds * 1000:.2f} ms",
            (20, 338),
        )


def _view(impossible):
    puzzle = impossible_puzzle() if impossible else default_puzzle()
    return PuzzleView(puzzle, solve_puzzle(puzzle))


def run():
    pygame.init()
    window = pygame.display.set_mode(SIZE)
    pygame.display.set_caption("Switch puzzle")
    impossible = False
    view = _view(impossible)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                view.apply_next()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                view.reset()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                impossible = not impossible
                view = _view(impossible)
        view.draw(window)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    run()
