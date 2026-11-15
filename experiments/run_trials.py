"""Benchmark A* against Uniform-Cost Search, and the CSP solver strategies.

Run from the project root:
    python -m experiments.run_trials            # 5 repeats per setting
    python -m experiments.run_trials --repeats 20

Writes experiments/results/astar_vs_ucs.csv and experiments/results/csp_strategies.csv.
Path length, cost, nodes explored and search effort are deterministic; only runtime
varies, so it is averaged over the repeats. A run that is not reproducible raises.
"""

import argparse
import csv
import statistics
from pathlib import Path

from ai.navigation import find_path
from game.levels import LEVELS
from game.state import WorldState
from puzzles.switch_puzzle import compare_strategies, default_puzzle, impossible_puzzle

RESULTS_DIR = Path(__file__).parent / "results"


def _grid(rows):
    return [[1 if ch == "#" else 0 for ch in row] for row in rows]


def _serpentine(size):
    """Walls across every other row with the gap alternating sides: a long forced route."""
    grid = [[0] * size for _ in range(size)]
    for r in range(1, size - 1, 2):
        gap = size - 1 if (r // 2) % 2 == 0 else 0
        for c in range(size):
            if c != gap:
                grid[r][c] = 1
    return grid


# A wall down column 4 with gaps at the top and bottom rows.
WALL_GRID = _grid([
    "..........",
    "....#.....",
    "....#.....",
    "....#.....",
    "....#.....",
    "....#.....",
    "....#.....",
    "....#.....",
    "....#.....",
    "..........",
])

def _level_trips(level_id):
    """The three trips of a real run: to the key (door locked), then to the puzzle and exit (door open)."""
    world = WorldState(level_id)
    locked = world.get_ai_grid()
    world.door_unlocked = True
    unlocked = world.get_ai_grid()
    return {
        f"{level_id}_to_key": (locked, world.start_position, world.key_position, None),
        f"{level_id}_to_puzzle": (unlocked, world.key_position, world.puzzle_position, None),
        f"{level_id}_to_exit": (unlocked, world.puzzle_position, world.exit_position, None),
    }


# name: (grid, start, goal, extra blocked cells)
SCENARIOS = {
    **{name: trip for level_id in LEVELS for name, trip in _level_trips(level_id).items()},
    "open_10x10": ([[0] * 10 for _ in range(10)], (0, 0), (9, 9), None),
    # Corner to corner every cell between start and goal ties on f = g + h, so A* can't prune.
    "open_30x30_corner": ([[0] * 30 for _ in range(30)], (0, 0), (29, 29), None),
    "open_30x30_straight": ([[0] * 30 for _ in range(30)], (15, 0), (15, 29), None),
    "wall_detour": (WALL_GRID, (5, 0), (5, 9), None),
    "direct_route": (WALL_GRID, (0, 0), (0, 9), None),
    # The same trip after an obstacle closes the top gap: the replan must use the bottom one.
    "replan_after_block": (WALL_GRID, (0, 0), (0, 9), [(0, 4)]),
    "serpentine_15x15": (_serpentine(15), (0, 0), (14, 0), None),
    "no_route": (_grid(["..#..", "..#..", "..#.."]), (0, 0), (0, 4), None),
}

ALGORITHMS = {"A*": True, "UCS": False}  # name: use_heuristic


def _same_every_time(results, key):
    values = {str(r[key]) for r in results}
    if len(values) != 1:
        raise RuntimeError(f"{key} changed between repeats: {values}")
    return results[0][key]


def run_search_trials(scenarios=SCENARIOS, repeats=5):
    rows = []
    for name, (grid, start, goal, blocked) in scenarios.items():
        for algorithm, use_heuristic in ALGORITHMS.items():
            results = [find_path(grid, start, goal, blocked, use_heuristic) for _ in range(repeats)]
            runtimes = [r["runtime"] * 1000 for r in results]
            rows.append({
                "scenario": name,
                "algorithm": algorithm,
                "repeats": repeats,
                "found": _same_every_time(results, "found"),
                "path_length": _same_every_time(results, "path_length"),
                "cost": _same_every_time(results, "cost"),
                "nodes_explored": _same_every_time(results, "nodes_explored"),
                "runtime_ms_mean": round(statistics.mean(runtimes), 4),
                "runtime_ms_min": round(min(runtimes), 4),
            })
    return rows


def run_csp_trials(repeats=5):
    rows = []
    for label, make in (("default", default_puzzle), ("impossible", impossible_puzzle)):
        runs = [compare_strategies(make()) for _ in range(repeats)]
        for strategy in runs[0]:
            results = [run[strategy] for run in runs]
            effort = {(r.solved, r.stats.assignments, r.stats.backtracks) for r in results}
            if len(effort) != 1:
                raise RuntimeError(f"{label}/{strategy} changed between repeats: {effort}")
            solved, assignments, backtracks = effort.pop()
            runtimes = [r.stats.runtime_seconds * 1000 for r in results]
            rows.append({
                "puzzle": label,
                "strategy": strategy,
                "repeats": repeats,
                "solved": solved,
                "assignments": assignments,
                "backtracks": backtracks,
                "runtime_ms_mean": round(statistics.mean(runtimes), 4),
            })
    return rows


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def print_table(rows):
    headers = list(rows[0])
    widths = [max(len(h), *(len(str(r[h])) for r in rows)) for h in headers]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    for r in rows:
        print("  ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)

    for filename, rows in (
        ("astar_vs_ucs.csv", run_search_trials(repeats=args.repeats)),
        ("csp_strategies.csv", run_csp_trials(repeats=args.repeats)),
    ):
        path = write_csv(args.out / filename, rows)
        print(f"\n{path}")
        print_table(rows)


if __name__ == "__main__":
    main()
