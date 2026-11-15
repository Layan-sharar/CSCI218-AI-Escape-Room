"""RogueMind: the AI escape room.

Run: python main.py
Controls: SPACE play/pause, N single step, R reset, +/- speed (or click the buttons).

The simulation only advances by the time the playback controls allow, so
update(dt) can also be driven headlessly (see tests/test_integration.py).
"""

import pygame

import game.interactions as interactions
import game.movement as movement
import game.obstacles as obstacles
import game.renderer as renderer
from ai.agent_controller import AgentController
from ai.navigation import find_path
from game.state import WorldState
from puzzles.switch_puzzle import solve_puzzle
from ui.inspector import Inspector
from ui.playback_controls import Playback

LEVEL_ID = "ember_crypt"
CONTROLS_HEIGHT = 60

WAITING_GOALS = ("WAIT_FOR_SPIKES", "LEVEL_COMPLETE", "NO_AVAILABLE_GOAL")

world = None

# The Behavior Tree reads this dict; it is refreshed from the world every frame
game_state = {}
agent = AgentController(game_state)

inspector = Inspector()
plan = {"target": None, "path": None}
run = {"steps": 0, "goal": None}


def load(level_id=LEVEL_ID):
    """Start (or restart) a level from scratch."""
    global world
    world = WorldState(level_id)
    movement.load_level(level_id)
    obstacles.place_spikes(level_id)
    inspector.reset()
    plan.update(target=None, path=None)
    run.update(steps=0, goal=None)


def reset():
    load(world.level_id)


playback = Playback(on_reset=reset)


def log(source, message):
    inspector.record(run["steps"], source, message)


def planning_grid():
    """The world's blocked grid, with the door counted open once we hold the key.

    The robot unlocks the door when it reaches it, so routes may go through it.
    """
    grid = world.get_ai_grid()
    if world.has_key:
        row, col = world.door_position
        grid[row][col] = 0
    return grid


def apply_world_rules():
    """Run the interaction rules for the cell the robot is standing on."""
    position = (movement.robot_row, movement.robot_col)
    if position == world.player_position:
        return

    world.player_position = position
    run["steps"] += 1

    if interactions.collect_key(world):
        log("World", "Picked up the key")
    if interactions.unlock_door(world):
        log("World", "Unlocked the door")

    if position == world.puzzle_position and not world.puzzle_solved:
        result = solve_puzzle()
        inspector.from_puzzle(result)
        if interactions.complete_puzzle(world, result.solved):
            log("CSP", f"Puzzle solved ({result.stats.assignments} assignments)")

    if interactions.complete_level(world):
        log("World", "Reached the exit")


def follow(decision):
    """Ask A* for a route to the chosen target and hand it to movement."""
    target = decision["target"]
    at_target = (movement.robot_row, movement.robot_col) == target
    remaining = movement.route[movement.route_index:]

    if target is None or at_target:
        return

    grid = planning_grid()
    blocked_ahead = any(grid[row][col] for row, col in remaining)
    if target == plan["target"] and remaining and not blocked_ahead:
        return

    result = find_path(grid, world.player_position, target)
    if result["found"] and movement.set_route(result["path"]):
        inspector.from_path(result)
        plan.update(target=target, path=result["path"])
        reason = "Replanned around an obstacle" if blocked_ahead else "Route"
        log("A*", f"{reason} to {target}: {result['path_length']} steps, "
                  f"{result['nodes_explored']} nodes")
    elif not result["found"]:
        # Stop here; this only works once the robot is centred on a cell,
        # so it is retried every frame (and replans if the way opens again)
        movement.set_route([world.player_position])
        if (plan["target"], plan["path"]) != (target, None):
            inspector.from_path(result)
            plan.update(target=target, path=None)
            log("A*", f"No route to {target}")


def update(dt):
    """Advance the simulation by dt seconds. Returns the Behavior Tree's decision."""
    obstacles.update_spikes(dt)

    game_state.update(
        has_key=world.has_key,
        puzzle_solved=world.puzzle_solved,
        exit_open=world.exit_open,
        level_complete=world.level_complete,
        spikes_blocking=movement.is_next_crossing_blocked(),
        key_position=world.key_position,
        puzzle_position=world.puzzle_position,
        exit_position=world.exit_position,
    )

    # Ask the Behavior Tree what to do
    decision = agent.update()
    inspector.from_decision(decision, agent.tree)
    if decision["goal"] != run["goal"]:
        run["goal"] = decision["goal"]
        log("BT", f"Goal: {decision['goal']}")

    if decision["goal"] not in WAITING_GOALS:
        follow(decision)
        movement.move_towards_target(dt)
    else:
        movement.is_moving = False

    # Apply the rules for wherever the robot is now, so a single step shows at once
    apply_world_rules()

    inspector.update(
        keys=f"{int(world.has_key)}/1",
        position=world.player_position,
        step=run["steps"],
    )
    return decision


def draw(screen, map_rect):
    # Select animation based on movement
    if movement.is_moving:
        current_frames = renderer.walk_frames[movement.direction]
    else:
        current_frames = renderer.idle_frames

    # Update animation frame
    movement.update_animation(len(current_frames))

    # Draw dungeon, route, spikes and robot
    renderer.draw_level(screen, world)
    renderer.draw_path(screen, movement.route[movement.route_index:])

    spike_sprite = renderer.spike_frames[obstacles.get_spike_frame()]
    screen.blit(
        spike_sprite,
        renderer.grid_to_pixel(obstacles.spike_row, obstacles.spike_col)
    )

    screen.blit(
        current_frames[movement.frame_index % len(current_frames)],
        (round(movement.robot_x), round(movement.robot_y))
    )

    # Inspector on the right, playback controls under the map
    map_w, map_h = map_rect.size
    inspector.draw(screen, pygame.Rect(map_w, 0, Inspector.WIDTH, map_h + CONTROLS_HEIGHT))
    playback.draw(screen, pygame.Rect(0, map_h, map_w, CONTROLS_HEIGHT))


def main():
    pygame.init()

    map_w, map_h = renderer.window_size(LEVEL_ID)
    screen = pygame.display.set_mode(
        (map_w + Inspector.WIDTH, map_h + CONTROLS_HEIGHT)
    )
    pygame.display.set_caption("RogueMind | AI Escape Room")
    renderer.load_assets()
    load(LEVEL_ID)

    clock = pygame.time.Clock()
    running = True

    while running:
        # Time elapsed since previous frame (seconds)
        real_dt = clock.tick(60) / 1000.0

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                playback.handle_event(event)

        # Paused: the world stays frozen, only the drawing continues
        dt = playback.sim_dt(real_dt)
        if dt > 0:
            update(dt)
        else:
            movement.is_moving = False

        draw(screen, pygame.Rect(0, 0, map_w, map_h))

        # Update display
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
