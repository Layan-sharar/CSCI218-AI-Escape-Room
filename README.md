# RogueMind — AI Escape Room

**CSCI218 Foundations of Artificial Intelligence | University of Wollongong in Dubai | Autumn 2026**

RogueMind is a **2D autonomous AI escape-room simulation** built with Python and Pygame. An intelligent robot navigates a tile-based dungeon, collects a key, unlocks a door, solves a switch puzzle, and reaches the exit. The robot makes its own decisions and adapts to changing conditions rather than following a manually controlled or hard-coded route.

## Features

- **Autonomous goal selection:** A Behaviour Tree chooses the robot's next objective based on the current game state.
- **A* pathfinding:** Finds routes through a grid of walkable and blocked cells using the Manhattan-distance heuristic.
- **Collision-aware movement:** Follows adjacent grid waypoints with smooth, animated movement; checks routes against the current grid.
- **Dynamic navigation:** Recalculates paths when a remaining waypoint becomes blocked. Locked doors also change the navigable map when unlocked.
- **Timed spike traps:** The robot waits for a safe crossing window, accounting for estimated crossing time and a 0.15-second safety margin.
- **Constraint Satisfaction Problem (CSP):** Solves a five-switch puzzle subject to six constraints.
- **AI Inspector:** Displays the selected goal, Behaviour Tree decision, route statistics, puzzle progress, and recent events.
- **Experiment suite:** Compares A* with Uniform Cost Search (UCS) and benchmarks CSP solving strategies.

## Requirements

- **Python 3.10 or newer** (a recent Python 3 version is recommended)
- `pip`
- A desktop environment capable of opening a Pygame window
- The project's `assets/` directory (included in the repository)

All third-party Python dependencies are listed in [`requirements.txt`](requirements.txt):

- `pygame` — game window, graphics, animation, and input
- `pytest` — automated tests

## Installation

### 1. Get the project

Clone the repository, or use **Code → Download ZIP** on GitHub and extract it.

```bash
git clone https://github.com/Layan-sharar/CSCI218-AI-Escape-Room.git
cd CSCI218-AI-Escape-Room
```

> If you downloaded a ZIP instead of cloning, open a terminal inside the extracted project directory containing `main.py` and `requirements.txt`.

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Run the Game

From the project root (the folder containing `main.py`), run:

```bash
python main.py
```

A Pygame window will open with the dungeon on the left and the **AI Inspector** on the right. The robot runs autonomously; you do **not** need to control its movement with arrow keys.

The default playable level is **The Ember Crypt** (`LEVEL_ID = "ember_crypt"` in `main.py`). The `game/levels.py` module also defines **The Lower Crypt**.

### Controls

| Key / interface control | Action |
| --- | --- |
| **Space** or **Play / Pause** button | Pause or resume the simulation |
| **N** or **Step** button | Advance the simulation by one step |
| **R** or **Reset** button | Restart the current simulation |
| **-** button / key | Decrease simulation speed |
| **+** button / key | Increase simulation speed |
| Close window | Exit the game |

The speed controls support **0.5×, 1×, 2×, and 4×** simulation speeds. The game window is resizable.

## How the Autonomous Agent Works

The normal objective progression is:

1. **FIND_KEY** — navigate to and collect the key.
2. **UNLOCK_DOOR** — navigate to a reachable cell adjacent to the locked door, then unlock it.
3. **SOLVE_PUZZLE** — navigate to the switch chamber and solve its CSP.
4. **REACH_EXIT** — navigate to the exit once the door is unlocked and the puzzle is solved.
5. **LEVEL_COMPLETE** — register successful completion after reaching the open exit.

The Behaviour Tree gives **WAIT_FOR_SPIKES** higher priority than ordinary navigation goals while a planned crossing is unsafe. Waiting does not itself recalculate the A* route. When no accessible objective is available, the controller can report **NO_AVAILABLE_GOAL**.

### AI integration

```text
WorldState (current objectives and navigation grid)
                |
                v
Behaviour Tree / AgentController (choose goal)
                |
                v
A* Navigation (calculate path to target)
                |
                v
RobotMovement (follow waypoints and check collisions)
                |
                v
WorldState + Interactions (update progress)
                |
                +----> Pygame Renderer + AI Inspector
```

The controller chooses the objective; **A\*** plans the route; **RobotMovement** executes the waypoints. The **CSP solver** is invoked when the robot reaches the puzzle. These responsibilities are implemented in separate Python modules.

### Navigation and changing obstacles

The dungeon is represented as a grid: **`0` = walkable** and **`1` = blocked**. The current navigation grid includes walls, static obstacles, a locked door, and dynamic blocked cells. `main.py` checks whether the remaining route includes a newly blocked waypoint and requests another A* route when necessary. Timed spikes are handled by waiting for a sufficiently long safe crossing interval.

**Note:** Randomly spawning obstacles are not part of the standard gameplay loop. Dynamic blocked cells can be introduced programmatically for testing, and the dungeon includes changing door and timed-spike states.

## Project Structure

```text
CSCI218-AI-Escape-Room/
├── main.py                     # Pygame application and AI integration
├── requirements.txt            # Python dependencies
├── ai/
│   ├── astar.py                # A* search and UCS baseline
│   ├── navigation.py           # Pathfinding interface
│   ├── behavior_tree.py        # Selector, Sequence, Condition, Action
│   ├── agent_controller.py     # Goal selection and priorities
│   └── csp.py                  # Constraint satisfaction solver
├── game/
│   ├── levels.py               # Dungeon maps and objective positions
│   ├── state.py                # Robot and level state
│   ├── movement.py             # Waypoints, smooth movement, collision checks
│   ├── obstacles.py            # Timed spikes and dynamic blocked cells
│   ├── interactions.py         # Key, door, puzzle, and exit interactions
│   └── renderer.py             # Tile and sprite rendering
├── puzzles/
│   └── switch_puzzle.py        # Switch constraints and CSP strategies
├── ui/
│   ├── inspector.py            # AI Inspector panel
│   ├── playback_controls.py    # Pause, step, reset, speed controls
│   └── puzzle_view.py          # Puzzle visualisation
├── assets/                     # Tileset, animations, and robot sprites
├── tests/                      # Automated algorithm and integration tests
└── experiments/
    ├── run_trials.py           # Repeated benchmark runner
    └── results/                # Generated CSV outputs
```

## Run Automated Tests

Install the dependencies, then run from the project root:

```bash
python -m pytest -q
```

The test suite covers A* routefinding and edge cases, Behaviour Tree execution, controller goal selection, CSP solving, and movement with changing obstacles. Test results will be printed in the terminal.

## Reproduce the Experiments

Run the existing benchmark script from the project root:

```bash
python -m experiments.run_trials
```

By default, this repeats each setting **5 times**. To run more repetitions:

```bash
python -m experiments.run_trials --repeats 20
```

The script prints the results and writes:

- `experiments/results/astar_vs_ucs.csv` — A* versus UCS: route availability, path length, cost, explored nodes, and runtime statistics.
- `experiments/results/csp_strategies.csv` — CSP strategy comparisons: solution status, assignments, backtracks, and mean runtime.

The benchmark includes open grids, obstacle detours, a blocked-route scenario, a serpentine grid, and an unreachable destination. Runtime depends on the machine; structural search measurements are checked for consistency across repetitions.

## Third-Party Art Assets

The visual assets are credited to their respective creators:

- **Dungeon tileset:** [mwaayk — Pixel Art Dungeon Tileset (FREE)](https://mwaayk.itch.io/pixel-dungeon-tileset)
- **Robot sprite:** [scratchmasterj21 — Tiny Robot Workshop: Helper Robot (Free Sampler)](https://scratchmasterj21.itch.io/tinyrobotssample)

These are **third-party assets**, not original artwork made by the project team. Refer to the creators' pages for licensing and permitted use.

## Coursework and Contributions

Developed as a group project for **CSCI218 Foundations of Artificial Intelligence**, University of Wollongong in Dubai (Autumn 2026).

The repository's Git commit history records individual development contributions. The team's contribution table and project report are submitted separately as required by the subject guidelines.

