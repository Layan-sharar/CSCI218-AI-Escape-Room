import pygame
import game.levels as levels
from game.levels import get_grid
# Spike location on the grid
spike_row = 3
spike_col = 6

# Animation sequence
spike_sequence = [3, 4, 2, 1, 2, 4]
frame_durations = [2000, 150, 150, 2000, 150, 150]

frame_index = 0
last_spike_time = pygame.time.get_ticks()

# Only frame 3 is fully retracted
SAFE_FRAME = 3

# Extra safety time in seconds
SAFETY_MARGIN = 0.15


def update_spikes():
    global frame_index, last_spike_time

    current_time = pygame.time.get_ticks()

    # Handle elapsed animation frames
    while (
        current_time - last_spike_time
        >= frame_durations[frame_index]
    ):
        last_spike_time += frame_durations[frame_index]
        frame_index = (frame_index + 1) % len(spike_sequence)


def get_spike_frame():
    return spike_sequence[frame_index]


def is_spike_active(row, col):
    return (
        row == spike_row
        and col == spike_col
        and get_spike_frame() != SAFE_FRAME
    )


def get_remaining_safe_time():
    if get_spike_frame() != SAFE_FRAME:
        return 0.0

    current_time = pygame.time.get_ticks()
    elapsed = current_time - last_spike_time

    remaining_ms = frame_durations[frame_index] - elapsed

    return max(0.0, remaining_ms / 1000.0)


def get_spike_rect():
    # Collision area matches the spike tile
    x = round(spike_col * levels.cell_width)
    y = round(spike_row * levels.cell_height)

    return pygame.Rect(
        x,
        y,
        round(levels.cell_width),
        round(levels.cell_height)
    )


def can_cross_spikes(required_time):
    # Robot must enter while spikes are fully retracted
    if get_spike_frame() != SAFE_FRAME:
        return False

    return (
        get_remaining_safe_time()
        >= required_time + SAFETY_MARGIN
    )


# ---- Person D: obstacle handoff ----

def set_dynamic_obstacle(state, position, blocked=True):
    """Block or unblock a floor cell for a changing obstacle."""
    grid = get_grid(state.level_id)

    try:
        row, column = position
    except (TypeError, ValueError):
        return False

    if not isinstance(row, int) or not isinstance(column, int):
        return False

    # Only allow positions inside the map that are floor tiles.
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
