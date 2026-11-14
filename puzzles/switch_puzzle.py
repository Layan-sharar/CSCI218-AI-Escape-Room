"""The switch-chamber puzzle: five coloured switches, six written rules, one answer.

Interface for the rest of the game:
    result = solve_puzzle()          # PuzzleResult
    result.solved                    # True/False, tells the world whether the door may open
    result.settings                  # {"RED": True, ...} (True = ON), or None if unsolvable
    result.stats                     # assignments, backtracks, runtime_seconds
"""

from dataclasses import dataclass
from typing import Optional

from ai.csp import CSP, Constraint, SolveStats, solve

SWITCHES = ["RED", "BLUE", "GREEN", "YELLOW", "WHITE"]
ON, OFF = True, False

_RULES = [
    ("RED and BLUE: never both ON.", ("RED", "BLUE"), lambda r, b: not (r and b)),
    ("GREEN ON means YELLOW ON.", ("GREEN", "YELLOW"), lambda g, y: (not g) or y),
    ("BLUE and YELLOW must differ.", ("BLUE", "YELLOW"), lambda b, y: b != y),
    ("WHITE ON only if RED is ON.", ("WHITE", "RED"), lambda w, r: (not w) or r),
    ("GREEN must be ON.", ("GREEN",), lambda g: g),
    ("GREEN and WHITE must match.", ("GREEN", "WHITE"), lambda g, w: g == w),
]
_IMPOSSIBLE_EXTRA = ("WHITE must be OFF.", ("WHITE",), lambda w: not w)


@dataclass
class SwitchPuzzle:
    name: str
    switches: list
    rules: list
    csp: CSP


@dataclass
class PuzzleResult:
    solved: bool
    settings: Optional[dict]
    stats: SolveStats
    strategy: str


def _build(name: str, rules: list) -> SwitchPuzzle:
    csp = CSP(
        variables=list(SWITCHES),
        domains={s: [OFF, ON] for s in SWITCHES},
        constraints=[Constraint(scope, check, text) for text, scope, check in rules],
    )
    return SwitchPuzzle(name, list(SWITCHES), [text for text, _, _ in rules], csp)


def default_puzzle() -> SwitchPuzzle:
    return _build("Switch Chamber", _RULES)


def impossible_puzzle() -> SwitchPuzzle:
    """The same chamber with one extra rule that contradicts two others."""
    return _build("Broken Chamber", _RULES + [_IMPOSSIBLE_EXTRA])


def _strategy_name(mrv: bool, forward_checking: bool) -> str:
    parts = (["mrv"] if mrv else []) + (["forward_checking"] if forward_checking else [])
    return "+".join(parts) or "plain"


def solve_puzzle(
    puzzle: Optional[SwitchPuzzle] = None, mrv: bool = True, forward_checking: bool = True
) -> PuzzleResult:
    puzzle = puzzle or default_puzzle()
    result = solve(puzzle.csp, mrv=mrv, forward_checking=forward_checking)
    settings = {s: result.solution[s] for s in puzzle.switches} if result.success else None
    return PuzzleResult(result.success, settings, result.stats, _strategy_name(mrv, forward_checking))


def compare_strategies(puzzle: Optional[SwitchPuzzle] = None) -> dict:
    """Run plain backtracking and each improvement on the same puzzle, for the experiment table."""
    puzzle = puzzle or default_puzzle()
    options = [(False, False), (True, False), (False, True), (True, True)]
    results = [solve_puzzle(puzzle, mrv=m, forward_checking=f) for m, f in options]
    return {r.strategy: r for r in results}


def format_comparison(puzzle: Optional[SwitchPuzzle] = None) -> str:
    """Markdown table of search effort per strategy, ready to paste into the report."""
    rows = ["| Strategy | Solved | Assignments | Backtracks |", "|---|---|---|---|"]
    for name, result in compare_strategies(puzzle).items():
        s = result.stats
        rows.append(f"| {name} | {result.solved} | {s.assignments} | {s.backtracks} |")
    return "\n".join(rows)


if __name__ == "__main__":
    for label, puzzle in (("Default puzzle", default_puzzle()), ("Impossible puzzle", impossible_puzzle())):
        print(f"{label}\n{format_comparison(puzzle)}\n")
