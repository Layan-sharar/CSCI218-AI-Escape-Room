 person-d-world-rules
def move_player(state, new_position):
    """Move one tile if the destination is inside the map and unblocked."""
    current_row, current_column = state.player_position
    new_row, new_column = new_position

    # Only allow a move to one neighboring tile.

"""Autonomous robot movement for Member D's dungeon and WorldState.

A* supplies a route; the robot follows it automatically. No keyboard movement.
The caller updates spikes once per frame and calls robot.update(dt).
"""

import pygame

from game import obstacles
from game.levels import get_level
from game.renderer import CELL_SIZE, MARGIN_X, MAP_TOP


def move_player(state, new_position):
    """Member D's original logical movement and collision check (unchanged)."""
    current_row, current_column = state.player_position
    new_row, new_column = new_position

 main
    distance = abs(new_row - current_row) + abs(new_column - current_column)
    if distance != 1:
        return False

    grid = state.get_ai_grid()

 person-d-world-rules
    # Reject positions outside the map.

 main
    if new_row < 0 or new_row >= len(grid):
        return False
    if new_column < 0 or new_column >= len(grid[new_row]):
        return False
 person-d-world-rules

    # 1 means blocked: a wall or a locked door.

 main
    if grid[new_row][new_column] == 1:
        return False

    state.player_position = (new_row, new_column)
 person-d-world-rules
    return True

    return True


class RobotMovement:
    """Smooth, autonomous movement following A* waypoints in (row, column) form."""

    def __init__(self, state, speed=50):
        self.state = state
        self.speed = speed
        self.animation_delay = 200
        self.reset()

    @staticmethod
    def grid_to_pixel(row, col):
        """Top-left of a 32px sprite in Member D's dungeon."""
        return float(MARGIN_X + col * CELL_SIZE), float(MAP_TOP + row * CELL_SIZE)

    def reset(self):
        self.state.reset()
        self.route = [self.state.player_position]
        self.route_index = 1
        self.robot_row, self.robot_col = self.state.player_position
        self.robot_x, self.robot_y = self.grid_to_pixel(self.robot_row, self.robot_col)
        self.direction = 'south'
        self.is_moving = False
        self.frame_index = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.current_animation = ('idle', 'south')
        self.crossing_spikes = False
        self.crossing_exit_index = None

    def _navigation_grid(self):
        """Use WorldState collision rules; spike tiles are time-gated, not walls.

        IMPORTANT: levels.py must exclude 'spike_traps' from STATIC_BLOCKING_FIELDS,
        so move_player() also accepts a safe spike tile.
        """
        return self.state.get_ai_grid()

    def set_route(self, new_route):
        """Accept Member B's result['path'] when the robot is centered on a tile."""
        if self.crossing_spikes or not new_route:
            return False
        positions = list(new_route)
        if not all(isinstance(p, (tuple, list)) and len(p) == 2
                   and all(isinstance(v, int) for v in p) for p in positions):
            return False
        positions = [tuple(p) for p in positions]
        if positions[0] != self.state.player_position:
            return False
        cx, cy = self.grid_to_pixel(*self.state.player_position)
        if abs(self.robot_x - cx) > 0.01 or abs(self.robot_y - cy) > 0.01:
            return False
        grid = self._navigation_grid()
        for row, col in positions:
            if not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
                return False
            if grid[row][col] != 0:
                return False
        if any(abs(a[0]-b[0]) + abs(a[1]-b[1]) != 1
               for a, b in zip(positions, positions[1:])):
            return False
        self.route = positions
        self.route_index = 1
        self.is_moving = False
        return True

    def _crossing_plan(self):
        """Calculate safe time to pass all consecutive spikes, even around corners.

        The original implementation rejected a turn *inside* the crossing.
        If A* picked a spike at a corner, the Behavior Tree would wait forever
        because no animation frame could make that geometric route "straight".
        Here we sum the actual orthogonal waypoint distances until the first
        non-spike tile (fully clear of the hazard). The existing safe-window
        timing and safety margin are still enforced by can_cross_spikes().
        """
        if self.route_index >= len(self.route):
            return None

        traps = set(get_level(self.state.level_id).get('spike_traps', []))
        if self.route[self.route_index] not in traps:
            return None

        last_spike_index = self.route_index
        distance = 0.0
        previous_x, previous_y = self.robot_x, self.robot_y
        previous_cell = self.state.player_position

        for index in range(self.route_index, len(self.route)):
            cell = self.route[index]
            if abs(cell[0] - previous_cell[0]) + abs(cell[1] - previous_cell[1]) != 1:
                return None

            x, y = self.grid_to_pixel(*cell)
            distance += pygame.Vector2(x - previous_x, y - previous_y).length()
            previous_x, previous_y = x, y
            previous_cell = cell

            if cell not in traps:
                return last_spike_index, distance / self.speed
            last_spike_index = index

        return None

    def is_next_crossing_blocked(self):
        if self.crossing_spikes or self.route_index >= len(self.route):
            return False
        traps = set(get_level(self.state.level_id).get('spike_traps', []))
        if self.route[self.route_index] not in traps:
            return False
        plan = self._crossing_plan()
        return plan is None or not obstacles.can_cross_spikes(plan[1])

    def update(self, dt):
        """Advance one animation tick; return True only when position changes."""
        self.is_moving = False
        if dt <= 0 or self.route_index >= len(self.route):
            return False
        target = self.route[self.route_index]
        if abs(target[0]-self.robot_row) + abs(target[1]-self.robot_col) != 1:
            return False

        if not self.crossing_spikes and self.is_next_crossing_blocked():
            return False
        if not self.crossing_spikes:
            plan = self._crossing_plan()
            if plan is not None:
                self.crossing_spikes = True
                self.crossing_exit_index = plan[0]

        # Reject newly blocked tiles before even starting the visual transition.
        grid = self._navigation_grid()
        if grid[target[0]][target[1]] != 0:
            self.crossing_spikes = False
            self.crossing_exit_index = None
            return False

        target_x, target_y = self.grid_to_pixel(*target)
        offset = pygame.Vector2(target_x-self.robot_x, target_y-self.robot_y)
        distance = offset.length()
        if distance:
            self.direction = ('east' if offset.x > 0 else 'west') if abs(offset.x) > abs(offset.y) else ('south' if offset.y > 0 else 'north')
        step = self.speed * dt
        if distance <= step:
            # Validate with Member D's unchanged move_player before updating
            # the visual position; never let the sprite and WorldState diverge.
            if not move_player(self.state, target):
                self.crossing_spikes = False
                self.crossing_exit_index = None
                return False
            self.robot_x, self.robot_y = target_x, target_y
            self.robot_row, self.robot_col = target
            self.route_index += 1
            if self.crossing_spikes and self.crossing_exit_index is not None and self.route_index > self.crossing_exit_index + 1:
                self.crossing_spikes = False
                self.crossing_exit_index = None
            self.is_moving = self.route_index < len(self.route)
            return True
        self.robot_x += offset.x / distance * step
        self.robot_y += offset.y / distance * step
        self.is_moving = True
        return False

    def update_animation(self, frame_count):
        if frame_count <= 0:
            return
        now = pygame.time.get_ticks()
        animation = ('walk', self.direction) if self.is_moving else ('idle', 'south')
        if animation != self.current_animation:
            self.current_animation = animation
            self.frame_index = 0
            self.last_frame_time = now
        elif now - self.last_frame_time >= self.animation_delay:
            self.frame_index = (self.frame_index + 1) % frame_count
            self.last_frame_time = now
 main
