import pygame
import game.renderer as renderer

# Spike cell for each level: a straight 1-wide corridor on the way to the key,
# so the robot always crosses it in a straight line
SPIKE_CELLS = {
    "ember_crypt": (12, 17),
    "lower_crypt": (16, 23),
}

# Spike location on the grid
spike_row, spike_col = SPIKE_CELLS["ember_crypt"]


def place_spikes(level_id):
    """Move the spikes to a level's cell and restart their cycle."""
    global spike_row, spike_col, frame_index, last_spike_time, sim_time
    spike_row, spike_col = SPIKE_CELLS[level_id]
    frame_index = 0
    last_spike_time = 0
    sim_time = 0

# Animation sequence
spike_sequence = [3, 4, 2, 1, 2, 4]
frame_durations = [2000, 150, 150, 2000, 150, 150]

# Simulation clock in ms, advanced by update_spikes(dt), so pausing the
# simulation also pauses the spikes
sim_time = 0

frame_index = 0
last_spike_time = 0

# Only frame 3 is fully retracted
SAFE_FRAME = 3

# Extra safety time in seconds
SAFETY_MARGIN = 0.15


def update_spikes(dt):
    """Advance the spike cycle by dt seconds of simulation time."""
    global frame_index, last_spike_time, sim_time

    sim_time += dt * 1000
    current_time = sim_time

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

    elapsed = sim_time - last_spike_time

    remaining_ms = frame_durations[frame_index] - elapsed

    return max(0.0, remaining_ms / 1000.0)


def get_spike_rect():
    # Collision area matches the spike tile
    x, y = renderer.grid_to_pixel(spike_row, spike_col)

    return pygame.Rect(
        x,
        y,
        renderer.CELL_SIZE,
        renderer.CELL_SIZE
    )


def can_cross_spikes(required_time):
    # Robot must enter while spikes are fully retracted
    if get_spike_frame() != SAFE_FRAME:
        return False

    return (
        get_remaining_safe_time()
        >= required_time + SAFETY_MARGIN
    )
