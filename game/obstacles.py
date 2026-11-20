"""Timed spike hazards and dynamic obstacle management for RogueMind.

Spike timing is driven by simulation dt, so pause/step/speed affect hazards
and robot movement consistently. 
"""
import pygame
from game.levels import get_grid, get_level

spike_sequence = [3, 4, 2, 1, 2, 4]
frame_durations = [2000, 150, 150, 2000, 150, 150]
frame_index = 0
elapsed_in_frame_ms = 0.0
SAFE_FRAME = 3
SAFETY_MARGIN = 0.15


def reset_spikes():
    global frame_index, elapsed_in_frame_ms
    frame_index = 0
    elapsed_in_frame_ms = 0.0


def update_spikes(dt=0.0):
    """Advance the spike cycle by simulation seconds (not wall-clock time)."""
    global frame_index, elapsed_in_frame_ms
    if dt <= 0:
        return
    elapsed_in_frame_ms += dt * 1000.0
    while elapsed_in_frame_ms >= frame_durations[frame_index]:
        elapsed_in_frame_ms -= frame_durations[frame_index]
        frame_index = (frame_index + 1) % len(spike_sequence)


def get_spike_frame():
    return spike_sequence[frame_index]


def is_spike_active(row, col, level_id="ember_crypt"):
    return ((row, col) in get_level(level_id).get("spike_traps", [])
            and get_spike_frame() != SAFE_FRAME)


def get_remaining_safe_time():
    if get_spike_frame() != SAFE_FRAME:
        return 0.0
    return max(0.0, (frame_durations[frame_index] - elapsed_in_frame_ms) / 1000.0)


def get_spike_rect(row, col, cell_size=32, margin_x=24, map_top=70):
    return pygame.Rect(margin_x + col * cell_size,
                       map_top + row * cell_size, cell_size, cell_size)


def can_cross_spikes(required_time):
    if get_spike_frame() != SAFE_FRAME:
        return False
    return get_remaining_safe_time() >= required_time + SAFETY_MARGIN


def set_dynamic_obstacle(state, position, blocked=True):
    grid = get_grid(state.level_id)
    try:
        row, column = position
    except (TypeError, ValueError):
        return False
    if not isinstance(row, int) or not isinstance(column, int):
        return False
    if row < 0 or row >= len(grid):
        return False
    if column < 0 or column >= len(grid[row]):
        return False
    if grid[row][column] != 0:
        return False
    cell = (row, column)
    if blocked:
        state.dynamic_obstacles.add(cell)
    else:
        state.dynamic_obstacles.discard(cell)
    return True
