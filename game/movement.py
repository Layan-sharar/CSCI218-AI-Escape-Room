
import pygame
import game.levels as levels
import game.obstacles as obstacles

# Temporary route using (row, column)
route = [
    (3, 4),  # Start
    (3, 5),  # Approach spikes
    (3, 6),  # Cross spikes (1st time)
    (3, 7),
    (3, 6),  # Cross spikes (2nd time)
    (3, 5),
    (3, 6),  # Cross spikes (3rd time)
    (3, 7),
    (3, 6),  # Cross spikes (4th time)
    (3, 5),
    (3, 4)   # Return to start
]

# Robot starting position
robot_row, robot_col = route[0]
robot_x, robot_y = levels.grid_to_pixel(robot_row, robot_col)

route_index = 1
speed = 160  # Pixels per second

# Animation settings
frame_index = 0
last_frame_time = pygame.time.get_ticks()
animation_delay = 200

direction = "south"
is_moving = False
current_animation = ("idle", "south")

# Spike-crossing state
crossing_spikes = False
crossing_exit_index = None

def set_route(new_route):
    """
    Replace the current route with a new path.

    Expected format:
    [(row, col), (row, col), ...]
    """
    global route, route_index
    global crossing_spikes, crossing_exit_index
    global is_moving

    # Never replace a route halfway through a spike crossing
    if crossing_spikes:
        return False

    # Reject empty paths
    if not new_route:
        return False

    # Convert to a list so the caller's path isn't modified
    new_route = list(new_route)

    # Validate every grid position
    for position in new_route:
        if (
            not isinstance(position, (tuple, list))
            or len(position) != 2
        ):
            return False

        row, col = position

        if (
            not isinstance(row, int)
            or not isinstance(col, int)
            or not levels.is_walkable(row, col)
        ):
            return False

    # Ensure each step is adjacent
    for previous, current in zip(new_route, new_route[1:]):
        distance = (
            abs(current[0] - previous[0])
            + abs(current[1] - previous[1])
        )

        if distance != 1:
            return False

    # The path must start at the robot's current cell
    if tuple(new_route[0]) != (robot_row, robot_col):
        return False

    # Don't replace the route while between grid cells
    current_x, current_y = levels.grid_to_pixel(
        robot_row, robot_col
    )

    if (
        abs(robot_x - current_x) > 0.01
        or abs(robot_y - current_y) > 0.01
    ):
        return False

    route = [tuple(position) for position in new_route]
    route_index = 1

    crossing_spikes = False
    crossing_exit_index = None
    is_moving = False

    return True


def robot_rect_at(x, y):
    """Return the robot's collision rectangle."""
    return pygame.Rect(
        round(x),
        round(y),
        levels.robot_width,
        levels.robot_height
    )


def get_safe_crossing_plan():
    """
    Find the route waypoint where the robot completely
    clears the spike trap.

    Returns (exit_index, required_time), or None.
    """
    if route_index >= len(route):
        return None

    spike_rect = obstacles.get_spike_rect()

    start_row, start_col = route[route_index - 1]
    target_row, target_col = route[route_index]

    dr = target_row - start_row
    dc = target_col - start_col

    if abs(dr) + abs(dc) != 1:
        return None

    total_distance = 0.0
    previous_x = robot_x
    previous_y = robot_y

    for i in range(route_index, len(route)):
        row, col = route[i]
        previous_row, previous_col = route[i - 1]

        # Continue straight until the robot clears the trap
        if (row - previous_row, col - previous_col) != (dr, dc):
            return None

        if not levels.is_walkable(row, col):
            return None

        x, y = levels.grid_to_pixel(row, col)

        total_distance += pygame.Vector2(
            x - previous_x,
            y - previous_y
        ).length()

        previous_x, previous_y = x, y

        # Stop once the robot is fully outside the spike area
        if not robot_rect_at(x, y).colliderect(spike_rect):
            return i, total_distance / speed

    return None


def is_next_crossing_blocked():
    """
    Tell the Agent Controller whether the upcoming
    spike crossing is currently unsafe.
    """
    if route_index >= len(route):
        return False

    # Never interrupt an ongoing crossing
    if crossing_spikes:
        return False

    target_row, target_col = route[route_index]

    target_x, target_y = levels.grid_to_pixel(
        target_row, target_col
    )

    spike_rect = obstacles.get_spike_rect()

    current_rect = robot_rect_at(robot_x, robot_y)
    target_rect = robot_rect_at(target_x, target_y)

    approaching_spikes = (
        current_rect.colliderect(spike_rect)
        or target_rect.colliderect(spike_rect)
    )

    if not approaching_spikes:
        return False

    plan = get_safe_crossing_plan()

    if plan is None:
        return True

    exit_index, required_time = plan

    return not obstacles.can_cross_spikes(required_time)


def move_towards_target(dt):
    """Move the robot toward its next route waypoint."""
    global robot_x, robot_y, robot_row, robot_col
    global route_index, direction, is_moving
    global crossing_spikes, crossing_exit_index

    # Default to idle unless actual movement occurs
    is_moving = False

    if route_index >= len(route) or dt <= 0:
        return

    target_row, target_col = route[route_index]

    # Only allow adjacent grid movements
    if (
        abs(target_row - robot_row)
        + abs(target_col - robot_col)
        != 1
    ):
        return

    # Prevent walking into walls
    if not levels.is_walkable(target_row, target_col):
        return

    target_x, target_y = levels.grid_to_pixel(
        target_row, target_col
    )

    spike_rect = obstacles.get_spike_rect()

    current_rect = robot_rect_at(robot_x, robot_y)
    target_rect = robot_rect_at(target_x, target_y)

    approaching_spikes = (
        not crossing_spikes
        and (
            current_rect.colliderect(spike_rect)
            or target_rect.colliderect(spike_rect)
        )
    )

    # Check safety before committing to a crossing
    if approaching_spikes:
        plan = get_safe_crossing_plan()

        if plan is None:
            return

        exit_index, required_time = plan

        if not obstacles.can_cross_spikes(required_time):
            return

        crossing_spikes = True
        crossing_exit_index = exit_index

    # Calculate direction and distance to target
    offset = pygame.Vector2(
        target_x - robot_x,
        target_y - robot_y
    )

    distance = offset.length()
    step = speed * dt

    if distance > 0:
        if abs(offset.x) > abs(offset.y):
            direction = "east" if offset.x > 0 else "west"
        else:
            direction = "south" if offset.y > 0 else "north"

    # Arrive at the next waypoint
    if distance <= step:
        robot_x, robot_y = target_x, target_y
        robot_row, robot_col = target_row, target_col
        route_index += 1

        # End the committed crossing once fully clear
        if (
            crossing_spikes
            and crossing_exit_index is not None
            and route_index > crossing_exit_index
        ):
            crossing_spikes = False
            crossing_exit_index = None

        # Idle after the final waypoint
        is_moving = route_index < len(route) and distance > 0

    elif distance > 0:
        # Smooth movement between grid cells
        displacement = offset / distance * step
        robot_x += displacement.x
        robot_y += displacement.y
        is_moving = True


def update_animation(frame_count):
    """Switch between walking and idle animations."""
    global frame_index, last_frame_time, current_animation

    current_time = pygame.time.get_ticks()

    animation = (
        ("walk", direction)
        if is_moving
        else ("idle", "south")
    )

    # Restart the animation when the state changes
    if animation != current_animation:
        current_animation = animation
        frame_index = 0
        last_frame_time = current_time
        return

    # Advance to the next animation frame
    if current_time - last_frame_time >= animation_delay:
        frame_index = (frame_index + 1) % frame_count
        last_frame_time = current_time


def reset_movement():
    """Restore the robot to its starting position."""
    global robot_row, robot_col, robot_x, robot_y
    global route_index, crossing_spikes, crossing_exit_index
    global is_moving, direction, frame_index
    global current_animation, last_frame_time

    robot_row, robot_col = route[0]
    robot_x, robot_y = levels.grid_to_pixel(robot_row, robot_col)

    route_index = 1
    crossing_spikes = False
    crossing_exit_index = None

    is_moving = False
    direction = "south"
    frame_index = 0
    current_animation = ("idle", "south")
    last_frame_time = pygame.time.get_ticks()
