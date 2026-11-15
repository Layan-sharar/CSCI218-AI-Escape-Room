import pygame

import game.interactions as interactions
from ai.agent_controller import AgentController
from ai.navigation import find_path
from game.state import WorldState
from puzzles.switch_puzzle import solve_puzzle

LEVEL_ID = "ember_crypt"

pygame.init()

world = WorldState(LEVEL_ID)

# The Behavior Tree reads this dict; it is refreshed from the world every frame
game_state = {}
agent = AgentController(game_state)

import game.renderer as renderer

# Create the window before loading images
screen = pygame.display.set_mode(renderer.window_size(LEVEL_ID))
renderer.load_assets()

import game.movement as movement
import game.obstacles as obstacles


def reset():
    world.reset()
    movement.load_level(LEVEL_ID)
    obstacles.place_spikes(LEVEL_ID)
    plan.update(target=None, path=None)


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
    interactions.collect_key(world)
    interactions.unlock_door(world)

    if position == world.puzzle_position and not world.puzzle_solved:
        interactions.complete_puzzle(world, solve_puzzle().solved)

    interactions.complete_level(world)


def follow(decision):
    """Ask A* for a route to the chosen target and hand it to movement."""
    target = decision["target"]
    at_target = (movement.robot_row, movement.robot_col) == target
    route_done = movement.route_index >= len(movement.route)

    if target is None or at_target:
        return
    if target == plan["target"] and not route_done:
        return

    result = find_path(planning_grid(), world.player_position, target)
    if result["found"] and movement.set_route(result["path"]):
        plan.update(target=target, path=result["path"])


plan = {"target": None, "path": None}
reset()
pygame.display.set_caption("RogueMind")

clock = pygame.time.Clock()
running = True

while running:
    # Time elapsed since previous frame (seconds)
    dt = clock.tick(60) / 1000.0

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset()

    # Update obstacle animations
    obstacles.update_spikes()

    apply_world_rules()

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
    pygame.display.set_caption(
        f"RogueMind | AI Decision: {decision['goal']}"
    )

    if decision["goal"] not in (
        "WAIT_FOR_SPIKES",
        "LEVEL_COMPLETE",
        "NO_AVAILABLE_GOAL"
    ):
        follow(decision)
        movement.move_towards_target(dt)

    else:
        movement.is_moving = False

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

    # Update display
    pygame.display.flip()

pygame.quit()
