# CSCI218-AI-Escape-Room

RogueMind: an AI robot escapes a pygame dungeon using a Behaviour Tree, A* and a CSP puzzle solver.

## Setup

pygame has no wheels for Python 3.14 yet (a source build can't load PNGs), so use Python 3.12 or 3.13:

    python3.12 -m venv .venv
    .venv/bin/pip install -r requirements.txt

## Run

    python main.py                      # the game, with the AI Inspector and playback controls
    python -m experiments.run_trials    # A* vs UCS and CSP benchmarks -> experiments/results/*.csv
    python -m pytest                    # all tests, including the full-run integration tests
    python -m game.world_demo           # console demo of the world rules

Game controls: SPACE play/pause, N single step, R reset, +/- speed (or click the buttons).

## Credits

Helper Robot by scratchmasterj21 (Tiny Robot Workshop).
